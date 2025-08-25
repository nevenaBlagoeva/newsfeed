import json
import pytest
from unittest.mock import MagicMock
from newsfeed.lambdas.ingest.ingest_lambda import lambda_handler
from newsfeed.shared.news_item import NewsItem

@pytest.fixture
def sample_event():
    return {
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

def test_lambda_processes_valid_item(sample_event):
    mock_client = MagicMock()
    mock_client.event_exists.return_value = False

    result = lambda_handler(sample_event, None, db_client=mock_client)

    assert result["processed"] == 1
    assert result["skipped"] == 0
    mock_client.put_item.assert_called_once()

def test_lambda_skips_duplicate(sample_event):
    mock_client = MagicMock()
    mock_client.event_exists.return_value = True

    result = lambda_handler(sample_event, None, db_client=mock_client)

    assert result["processed"] == 0
    assert result["skipped"] == 1
    mock_client.put_item.assert_not_called()

def test_lambda_skips_invalid_item(sample_event, monkeypatch):
    # Patch NewsItem.validate to return False
    monkeypatch.setattr(NewsItem, "validate", lambda self: False)
    mock_client = MagicMock()

    result = lambda_handler(sample_event, None, db_client=mock_client)

    assert result["processed"] == 0
    assert result["skipped"] == 1
    mock_client.put_item.assert_not_called()
