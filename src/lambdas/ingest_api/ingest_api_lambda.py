import json
import boto3
import os
from typing import Dict, Any, List
from shared.news_item import NewsItem

# Initialize DynamoDB client at module level
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE_NAME')
table = dynamodb.Table(table_name) if table_name else None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """API Gateway Lambda for ingesting news events directly"""
    
    if not table:
        raise ValueError("DYNAMODB_TABLE_NAME environment variable not set")
    
    try:
        # Parse the request body
        if 'body' in event:
            # API Gateway format
            body = json.loads(event['body'])
        else:
            # Direct invocation format
            body = event
        
        # Ensure body is a list
        events_data = body if isinstance(body, list) else [body]
        
        print(f"Processing {len(events_data)} events from API call")
        
        processed = 0
        errors = []
        
        for i, event_data in enumerate(events_data):
            try:
                # Validate required fields
                if not _validate_event(event_data):
                    errors.append(f"Event {i}: Missing required fields")
                    continue
                
                # Create NewsItem from the event
                news_item = NewsItem.from_raw_event(event_data)
                
                # Check for duplicates
                if _event_exists(news_item.fingerprint):
                    print(f"Duplicate event skipped: {news_item.title[:50]}...")
                    continue
                
                # Save to DynamoDB
                table.put_item(Item=news_item.to_dynamodb_item())
                processed += 1
                
            except Exception as e:
                errors.append(f"Event {i}: {str(e)}")
        
        print(f"API ingestion completed: processed {processed}, errors {len(errors)}")
        
        # Return API Gateway response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Events processed successfully',
                'processed': processed,
                'total': len(events_data),
                'errors': errors if errors else None
            })
        }
        
    except Exception as e:
        print(f"API ingestion error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Invalid request',
                'message': str(e)
            })
        }

def _validate_event(event_data: Dict[str, Any]) -> bool:
    """Validate that event has required fields"""
    required_fields = ['id', 'source', 'title', 'published_at']
    return all(field in event_data and event_data[field] for field in required_fields)

def _event_exists(fingerprint: str) -> bool:
    """Check if event already exists in DynamoDB"""
    try:
        response = table.get_item(
            Key={'id': fingerprint},
            ProjectionExpression='id'
        )
        return 'Item' in response
    except Exception as e:
        print(f"Error checking for duplicate: {str(e)}")
        return False
