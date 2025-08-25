import json
import os
import logging
from typing import Dict, Any
from newsfeed.shared.dynamodb_client import DynamoDBClient
from newsfeed.shared.news_item import NewsItem

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any, db_client: DynamoDBClient = None) -> Dict[str, int]:
    """
    Processes SQS messages, validates them, checks for duplicates, and stores in DynamoDB.
    `db_client` can be injected for testing; defaults to real DynamoDB.
    """
    table_name = 'RawEvents'

    # Use injected client or create a new one
    if db_client is None:
        db_client = DynamoDBClient(table_name)

    logger.info(f"Processing {len(event['Records'])} SQS messages")
    processed, skipped = 0, 0

    for record in event["Records"]:
        try:
            message_body = json.loads(record["body"])
            news_item = NewsItem.from_raw_event(message_body)

            if not news_item.validate():
                logger.warning("Invalid event structure, skipping")
                skipped += 1
                continue

            if db_client.event_exists(news_item.fingerprint):
                logger.info(f"Duplicate event found: {news_item.title[:50]}...")
                skipped += 1
                continue

            db_client.put_item(news_item.to_dynamodb_item())
            processed += 1

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    logger.info(f"Completed: processed {processed}, skipped {skipped}")
    return {"processed": processed, "skipped": skipped}
