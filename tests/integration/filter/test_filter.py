import boto3
import pytest
from moto import mock_dynamodb
from newsfeed.lambdas.filter import filter_lambda
from newsfeed.shared.dynamodb_client import DynamoDBClient

@pytest.fixture
def dynamodb_table():
    with mock_dynamodb():
        table_name = "FilteredEvents"
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
def mock_dynamo_client(dynamodb_table):
    client = DynamoDBClient(dynamodb_table.name)
    client.table = dynamodb_table  # inject mocked table
    return client

def test_filter_lambda_adds_item(mock_dynamo_client):
    raw_item = {
        "id": "123",
        "title": "Python 3.12 Released",
        "source": "reddit",
        "published_at": "2025-08-24T12:00:00Z",
        "score": 100
    }
    event = {"Records": [{
        "dynamodb": {"NewImage": {k: {"S": str(v)} for k, v in raw_item.items()}}
    }]}

    result = filter_lambda.lambda_handler(event, None, db_client=mock_dynamo_client)
    assert result["processed"] == 1

    items = mock_dynamo_client.table.scan()["Items"]
    assert any(item["id"] == "123" for item in items)

def test_filter_lambda_skips_non_tech_article(mock_dynamo_client):
    raw_item = {
        "id": "456",
        "title": "Gardening Tips",
        "source": "reddit",
        "published_at": "2025-08-24T12:00:00Z",
        "score": 10
    }
    event = {"Records": [{
        "dynamodb": {"NewImage": {k: {"S": str(v)} for k, v in raw_item.items()}}
    }]}

    result = filter_lambda.lambda_handler(event, None, db_client=mock_dynamo_client)
    assert result["processed"] == 0

    items = mock_dynamo_client.table.scan()["Items"]
    assert all(item["id"] != "456" for item in items)
