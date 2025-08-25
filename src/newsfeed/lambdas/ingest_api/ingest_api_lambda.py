import json
import logging
from typing import Dict, Any, List, Optional
from newsfeed.shared.news_item import NewsItem
from newsfeed.shared.dynamodb_client import DynamoDBClient

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_db_client() -> DynamoDBClient:
    return DynamoDBClient('RawEvents')


def lambda_handler(event: Dict[str, Any], context: Any, db_client: Optional[DynamoDBClient] = None) -> Dict[str, Any]:
    """
    API Gateway Lambda for ingesting news events directly.
    db_client can be injected for tests.
    """
    logger.info("Processing API ingestion request")
    if db_client is None:
        db_client = get_db_client()

    try:
        events_data = _parse_event_body(event)
        logger.info(f"Processing {len(events_data)} events from API call")

        processed, errors = _process_events(events_data, db_client)

        logger.info(f"API ingestion completed: processed {processed}, errors {len(errors)}")

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
        logger.error(f"API ingestion error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Invalid request',
                'message': str(e)
            })
        }


def _parse_event_body(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract event list from API Gateway or direct invocation
    """
    if 'body' in event:
        body = json.loads(event['body'])
    else:
        body = event
    return body if isinstance(body, list) else [body]


def _process_events(events_data: List[Dict[str, Any]], db_client: DynamoDBClient) -> (int, List[str]):
    """Process multiple news events, validate and store them"""
    processed = 0
    errors = []

    logger.info(f"Processing {len(events_data)} events from API call")
    for i, event_data in enumerate(events_data):
        try:
            news_item = NewsItem.from_raw_event(event_data)

            logger.info(f"Processing {news_item} events from API call")
            if not news_item.validate():
                errors.append(f"Event {i}: Missing required fields")
                continue

            if db_client.event_exists(news_item.fingerprint):
                logger.info(f"Duplicate event skipped: {news_item.title[:50]}...")
                continue

            db_client.put_item(news_item.to_dynamodb_item())
            processed += 1

        except Exception as e:
            errors.append(f"Event {i}: {str(e)}")

    return processed, errors
