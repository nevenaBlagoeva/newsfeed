# tests/integration/test_retrieve_lambda_integration.py
from decimal import Decimal
import json
import pytest
import boto3
from moto import mock_dynamodb
from newsfeed.shared.dynamodb_client import DynamoDBClient
from newsfeed.lambdas.retrieve import retrieve_lambda

TABLE_NAME = "FilteredEvents"

@pytest.fixture
def dynamodb_table():
    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        yield table
        

def test_lambda_retrieves(dynamodb_table):

    db_client = DynamoDBClient(TABLE_NAME)

    db_client.put_item({
        'PK': 'news',
        'SK': '0.95#2025-08-24T12:00:00Z',
        'id': '1',
        'source': 'reddit',
        'title': 'Python 3.12 Released',
        'body': 'Some content',
        'published_at': '2025-08-24T12:00:00Z',
        'url': 'https://example.com',
        'relevance_score': Decimal('0.95')
    })

    event = {'queryStringParameters': None}
    resp = retrieve_lambda.lambda_handler(event, None, db_client=db_client)
    data = json.loads(resp['body'])
    assert len(data) == 1
    assert data[0]['title'] == 'Python 3.12 Released'


def test_lambda_table_retrieves_multiple_in_order(dynamodb_table):

    db_client = DynamoDBClient(TABLE_NAME)

    items = [
                {
            'PK': 'news',
            'SK': '0.90#2025-08-23T12:00:00Z',
            'id': '2',
            'source': 'twitter',
            'title': 'New Features in Python 3.12',
            'body': 'Some more content',
            'published_at': '2025-08-23T12:00:00Z',
            'url': 'https://example.com',
            'relevance_score': Decimal('0.90')
        },
        {
            'PK': 'news',
            'SK': '0.95#2025-08-24T12:00:00Z',
            'id': '1',
            'source': 'reddit',
            'title': 'Python 3.12 Released',
            'body': 'Some content',
            'published_at': '2025-08-24T12:00:00Z',
            'url': 'https://example.com',
            'relevance_score': Decimal('0.95')
        }
    ]

    for item in items:
        db_client.put_item(item)

    event = {'queryStringParameters': None}
    resp = retrieve_lambda.lambda_handler(event, None, db_client=db_client)
    data = json.loads(resp['body'])
    assert len(data) == 2
    assert data[0]['title'] == 'Python 3.12 Released'
    assert data[1]['title'] == 'New Features in Python 3.12'