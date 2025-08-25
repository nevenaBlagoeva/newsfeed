# tests/integration/test_api_lambda_integration.py
import json
import boto3
import pytest
from moto import mock_dynamodb
from newsfeed.shared.news_item import NewsItem
from newsfeed.lambdas.ingest_api import ingest_api_lambda
from newsfeed.shared.dynamodb_client import DynamoDBClient

TABLE_NAME = "RawEvents"

@pytest.fixture
def dynamodb_table():
    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        table.wait_until_exists()
        yield table

@pytest.fixture
def db_client(dynamodb_table):
    return DynamoDBClient(TABLE_NAME)

def test_lambda_handler_adds_items(db_client):
    events = [
        {
            "id": "1",
            "source": "reddit",
            "title": "Python 3.12 Released",
            "published_at": "2025-08-24T12:00:00Z",
            "body": "Some content"
        },
        {
            "id": "2",
            "source": "ars-technica",
            "title": "New Tech Article",
            "published_at": "2025-08-24T13:00:00Z",
            "body": "More content"
        }
    ]

    event = {"body": json.dumps(events)}

    result = ingest_api_lambda.lambda_handler(event, None, db_client=db_client)
    body = json.loads(result['body'])
    
    assert result['statusCode'] == 200
    assert body['processed'] == 2
    assert body['total'] == 2
    assert body['errors'] is None

    # Verify items are in DynamoDB
    stored_items = db_client.table.scan()["Items"]
    fingerprints = [NewsItem.from_raw_event(event).fingerprint for event in events]
    ids = [item['id'] for item in stored_items]
    assert len(fingerprints) == 2
    assert fingerprints[0] in ids and fingerprints[1] in ids

def test_lambda_handler_skips_invalid_and_duplicates(db_client):
    # Use the same fingerprint logic as the lambda    
    duplicate_article = {
        "id": "1",
        "source": "reddit",
        "title": "Python 3.12 Released",
        "published_at": "2025-08-24T12:00:00Z",
        "body": "Some content"
    }
    
    # Create NewsItem and insert using its fingerprint 
    news_item = NewsItem.from_raw_event(duplicate_article)
    db_client.put_item(news_item.to_dynamodb_item())

    events = [
        duplicate_article,  # Should be detected as duplicate
        {
            "id": "3",  # valid
            "source": "ars-technica",
            "title": "New Tech Article",
            "published_at": "2025-08-24T13:00:00Z"
        },
        {
            "id": "4",  # missing title
            "source": "reddit",
            "published_at": "2025-08-24T14:00:00Z"
        }
    ]

    event = {"body": json.dumps(events)}
    result = ingest_api_lambda.lambda_handler(event, None, db_client=db_client)
    body = json.loads(result['body'])

    # Debug output
    print(f"Result: {body}")
    print(f"Items in DB after test: {db_client.table.scan()['Items']}")

    assert body['processed'] == 1  # only id=3 processed
    assert len(body['errors']) == 1  # id=4 skipped
