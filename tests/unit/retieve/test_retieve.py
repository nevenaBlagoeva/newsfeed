# tests/unit/test_retrieve_lambda.py
import json
import pytest
from unittest.mock import MagicMock
from newsfeed.lambdas.retrieve import retrieve_lambda

@pytest.fixture
def mock_db_client():
    client = MagicMock()
    client.query.return_value = {
        'Items': [
            {
                'id': '1',
                'source': 'reddit',
                'title': 'Python 3.12 Released',
                'body': 'Some content',
                'published_at': '2025-08-24T12:00:00Z',
                'url': 'https://example.com',
                'SK': '0.95#2025-08-24T12:00:00Z',
                'relevance_score': 0.95
            }
        ]
    }
    return client

def test_lambda_handler_basic(mock_db_client):
    event = {'queryStringParameters': None}
    resp = retrieve_lambda.lambda_handler(event, None, db_client=mock_db_client)
    
    assert resp['statusCode'] == 200
    body = resp['body']
    data = json.loads(body)
    assert len(data) == 1
    assert data[0]['title'] == 'Python 3.12 Released'

def test_lambda_handler_with_metadata(mock_db_client):
    event = {'queryStringParameters': {'dashboard': 'true'}}
    resp = retrieve_lambda.lambda_handler(event, None, db_client=mock_db_client)
    data = json.loads(resp['body'])
    
    assert 'SK' in data[0]
    assert 'relevance_score' in data[0]

def test_format_events_no_metadata():
    items = [
        {'id': '1', 'source': 'reddit', 'title': 'Test', 'published_at': '2025-08-24'}
    ]
    formatted = retrieve_lambda._format_events(items, include_metadata=False)
    assert 'SK' not in formatted[0]
    assert formatted[0]['title'] == 'Test'
