import os
import json
import boto3
import pytest
from moto import mock_dynamodb
from newsfeed.shared.news_item import NewsItem
from newsfeed.lambdas.ingest import ingest_lambda
from newsfeed.shared.dynamodb_client import DynamoDBClient

@pytest.fixture
def dynamodb_table():
    with mock_dynamodb():
        table_name = "NewsEvents"
        os.environ["DYNAMODB_TABLE_NAME"] = table_name

        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield table

@pytest.fixture
def db_client(dynamodb_table):
    client = DynamoDBClient(dynamodb_table.name)
    client.table = dynamodb_table
    return client

def test_ingest_lambda_adds_item(db_client):
    event = {
        "Records": [
            {"body": json.dumps({
                "id": "123",
                "title": "Python 3.12 Released",
                "source": "reddit",
                "published_at": "2025-08-24T12:00:00Z",
                "score": 100,
                "url": "https://reddit.com/r/Python/comments/123"
            })}
        ]
    }

    result = ingest_lambda.lambda_handler(event, None, db_client=db_client)
    assert result["processed"] == 1
    assert result["skipped"] == 0

    items = db_client.table.scan()["Items"]
    print("Items in DynamoDB:", items)
    assert any(item["title"] == "Python 3.12 Released" for item in items)

def test_ingest_lambda_skips_duplicate(db_client):
    fingerprint = NewsItem.from_raw_event({
                "id": "123",
                "title": "Python 3.12 Released",
                "source": "reddit",
                "published_at": "2025-08-24T12:00:00Z",
                "score": 100,
                "url": "https://reddit.com/r/Python/comments/123"
            }).fingerprint
    
    print("Fingerprint of existing item:", fingerprint)
    db_client.put_item({
        "id": fingerprint,
        "title": "Python 3.12 Released",
        "source": "reddit",
        "published_at": "2025-08-24T12:00:00Z",
        "score": 100,
        "url": "https://reddit.com/r/Python/comments/123"
    })

    event = {
        "Records": [
            {"body": json.dumps({
                "id": "123",
                "title": "Python 3.12 Released",
                "source": "reddit",
                "published_at": "2025-08-24T12:00:00Z",
                "score": 100,
                "url": "https://reddit.com/r/Python/comments/123"
            })}
        ]
    }

    result = ingest_lambda.lambda_handler(event, None, db_client=db_client)
    assert result["processed"] == 0
    assert result["skipped"] == 1
