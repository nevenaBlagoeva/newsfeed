# tests/unit/test_api_lambda.py
import pytest
from unittest.mock import MagicMock
from newsfeed.lambdas.ingest_api import ingest_api_lambda
from newsfeed.shared.news_item import NewsItem

@pytest.fixture
def mock_db_client():
    client = MagicMock()
    client.event_exists.return_value = False
    client.put_item.return_value = None
    return client

def test_process_valid_events(mock_db_client):
    events = [
        {
            "id": "1",
            "source": "reddit",
            "title": "Python 3.12 Released",
            "published_at": "2025-08-24T12:00:00Z",
            "body": "Some content"
        }
    ]

    processed, errors = ingest_api_lambda._process_events(events, mock_db_client)

    assert processed == 1
    assert errors == []
    mock_db_client.put_item.assert_called_once()
    mock_db_client.event_exists.assert_called_once()

def test_process_invalid_event_skipped(mock_db_client):
    # Missing required field 'title'
    events = [
        {
            "id": "2",
            "source": "reddit",
            "published_at": "2025-08-24T12:00:00Z"
        }
    ]

    processed, errors = ingest_api_lambda._process_events(events, mock_db_client)

    assert processed == 0
    assert len(errors) == 1
    mock_db_client.put_item.assert_not_called()

def test_process_duplicate_event_skipped(mock_db_client):
    """Test that duplicate events are properly detected and skipped"""
    # Mock that event already exists
    mock_db_client.event_exists.return_value = True

    events = [
        {
            "id": "1",
            "source": "reddit",
            "title": "Python 3.12 Released",
            "published_at": "2025-08-24T12:00:00Z",
            "body": "Some content"
        }
    ]

    processed, errors = ingest_api_lambda._process_events(events, mock_db_client)

    assert processed == 0  # Should be skipped due to duplicate
    assert errors == []    # No errors, just skipped
    mock_db_client.put_item.assert_not_called()  # Should not try to put duplicate
