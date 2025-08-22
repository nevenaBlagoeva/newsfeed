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
    
    if not filtered_table:
        raise ValueError("FILTERED_TABLE_NAME environment variable not set")
    
    try:
        # Query parameters - handle None case
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 50))
        limit = min(limit, 100)  # Cap at 100 items
        
        print(f"Retrieving up to {limit} filtered events")
        
        # Query DynamoDB - get all items from 'news' partition, sorted by SK (relevance#timestamp)
        response = filtered_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('news'),
            ScanIndexForward=False,  # Descending order (highest relevance first)
            Limit=limit
        )
        
        items = response.get('Items', [])
        
        # Convert to the original JSON format (same shape as input)
        events = []
        for item in items:
            events.append({
                'id': item.get('id'),
                'source': item.get('source'),
                'title': item.get('title'),
                'body': item.get('body', ''),
                'published_at': item.get('published_at')
            })
        
        print(f"Retrieved {len(events)} filtered events")
        
        # Return just the events array (same format as input)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(events)  # Return events array directly
        }
        
    except Exception as e:
        print(f"Retrieve error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
