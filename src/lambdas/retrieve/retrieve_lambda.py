import json
import boto3
import os
from typing import Dict, Any, List
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
filtered_table_name = os.getenv('FILTERED_TABLE_NAME')
filtered_table = dynamodb.Table(filtered_table_name) if filtered_table_name else None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Retrieve filtered events sorted by relevance score"""
    
    # CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
    }
    
    if not filtered_table:
        raise ValueError("FILTERED_TABLE_NAME environment variable not set")
    
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        limit = min(int(query_params.get('limit', 50)), 100)
        
        # Check if request is from dashboard (includes debug/dashboard params)
        include_metadata = query_params.get('dashboard') == 'true' or query_params.get('debug') == 'true'
        
        print(f"Retrieving up to {limit} filtered events (metadata: {include_metadata})")
        
        # Query DynamoDB - get all items from 'news' partition, sorted by SK (relevance#timestamp)
        response = filtered_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('news'),
            ScanIndexForward=False,  # Descending order (highest relevance first)
            Limit=limit
        )
        
        items = response.get('Items', [])
        
        # Convert to JSON format based on request type
        events = []
        for item in items:
            event_data = {
                'id': item.get('id'),
                'source': item.get('source'),
                'title': item.get('title'),
                'body': item.get('body', ''),
                'published_at': item.get('published_at'),
                'url': item.get('url', '')  # Include URL for clickable links
            }
            
            # Include metadata only for dashboard requests
            if include_metadata:
                event_data['SK'] = item.get('SK')
                event_data['relevance_score'] = float(item.get('relevance_score', 0))
            
            events.append(event_data)
        
        print(f"Retrieved {len(events)} filtered events")
        
        # Return just the events array (same format as input)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps(events)  # Return events array directly
        }
        
    except Exception as e:
        print(f"Retrieve error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                **cors_headers
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
