import json
import boto3
import os
from typing import Dict, Any, Optional

# Import shared NewsItem module
from shared.news_item import NewsItem

# Initialize DynamoDB client at module level
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE_NAME')
table = dynamodb.Table(table_name) if table_name else None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    print(f"Processing {len(event['Records'])} SQS messages")
    
    if not table:
        raise ValueError("DYNAMODB_TABLE_NAME environment variable not set")
    
    processed = 0
    skipped = 0
    
    for record in event['Records']:
        try:
            # Parse SQS message body
            message_body = json.loads(record['body'])
            
            # Create NewsItem from raw event
            news_item = NewsItem.from_raw_event(message_body)
            
            # Validate required fields
            if not news_item.validate():
                print(f"Invalid event structure, skipping")
                skipped += 1
                continue
            
            # Check if event already exists
            if _event_exists(news_item.fingerprint):
                print(f"Duplicate event found: {news_item.title[:50]}...")
                skipped += 1
                continue
            
            # Save to DynamoDB
            table.put_item(Item=news_item.to_dynamodb_item())
            processed += 1
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            raise
    
    print(f"Completed: processed {processed}, skipped {skipped}")
    return {"processed": processed, "skipped": skipped}

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
