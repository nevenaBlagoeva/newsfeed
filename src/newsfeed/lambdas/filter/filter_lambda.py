import logging
from typing import Dict, Any
from newsfeed.lambdas.filter.ranker import calculate_relevance_score
from newsfeed.shared.dynamodb_client import DynamoDBClient
from newsfeed.lambdas.filter.create_filtered import create_filtered_item

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any, db_client: DynamoDBClient = None) -> Dict[str, int]:
    """
    Processes DynamoDB stream records, filters tech articles, and stores them.
    `db_client` can be injected for testing.
    """
    table_name = "FilteredEvents"
    if db_client is None:
        db_client = DynamoDBClient(table_name)

    records = event.get('Records', [])
    logger.info(f"Processing {len(records)} records")
    processed = 0

    for record in records:
        item = extract_stream_item(record)

        relevance_score = calculate_relevance_score(item, algorithm = 'word_score')
        logger.info(f"Calculated relevance score: {relevance_score}")
        if relevance_score > 0.4:  # Threshold for filtering
            filtered_item = create_filtered_item(item, relevance_score)
            db_client.put_item(filtered_item)
            processed += 1

    logger.info(f"Processed {processed} items")
    return {"processed": processed}


def extract_stream_item(record: dict):
    """Return a normalized Python dict from a DynamoDB stream record."""
    dynamodb_data = record.get("dynamodb", {})
    image = dynamodb_data.get("NewImage") or dynamodb_data.get("OldImage")
    if not image:
        return {}

    return {k: list(v.values())[0] for k, v in image.items()}