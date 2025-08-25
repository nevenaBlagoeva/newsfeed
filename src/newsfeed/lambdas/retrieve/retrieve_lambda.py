# src/lambdas/retrieve/retrieve_lambda.py
import json
import os
from typing import Dict, Any, List, Optional
from boto3.dynamodb.conditions import Key
from newsfeed.shared.dynamodb_client import DynamoDBClient
import logging

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_db_client(table_name: Optional[str] = None) -> DynamoDBClient:
    table_name = table_name or os.getenv('FILTERED_TABLE_NAME', 'FilteredEvents')
    return DynamoDBClient(table_name)

def lambda_handler(event: Dict[str, Any], context: Any, db_client: DynamoDBClient = None) -> Dict[str, Any]:
    """Retrieve filtered events, sorted by relevance score"""
    if db_client is None:
        db_client = get_db_client()

    cors_headers = {'Access-Control-Allow-Origin': '*'}

    try:
        query_params = event.get('queryStringParameters') or {}
        limit = min(int(query_params.get('limit', 50)), 100)
        include_metadata = query_params.get('dashboard') == 'true'

        logger.info(f"Retrieving up to {limit} filtered events (metadata: {include_metadata})")

        items = _query_filtered_events(db_client, limit)
        events = _format_events(items, include_metadata)

        logger.info(f"Retrieved {len(events)} filtered events")

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', **cors_headers},
            'body': json.dumps(events)
        }

    except Exception as e:
        logger.error(f"Retrieve error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', **cors_headers},
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }


def _query_filtered_events(db_client: DynamoDBClient, limit: int) -> List[Dict[str, Any]]:
    """Query DynamoDB for filtered news items in 'news' partition"""
    response = db_client.query(
        KeyConditionExpression=Key('PK').eq('news'),
        ScanIndexForward=False,  # descending
        Limit=limit
    )
    return response.get('Items', [])


def _format_events(items: List[Dict[str, Any]], include_metadata: bool) -> List[Dict[str, Any]]:
    """Convert DynamoDB items to API response format"""
    events = []
    for item in items:
        event_data = {
            'id': item.get('id'),
            'source': item.get('source'),
            'title': item.get('title'),
            'body': item.get('body', ''),
            'published_at': item.get('published_at'),
            'url': item.get('url', '')
        }
        if include_metadata:
            event_data['SK'] = item.get('SK')
            event_data['relevance_score'] = float(item.get('relevance_score', 0))
        events.append(event_data)
    return events
