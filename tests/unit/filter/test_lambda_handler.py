from newsfeed.lambdas.filter import filter_lambda
from unittest.mock import MagicMock


def test_lambda_handler_with_mock():
    mock_client = MagicMock()
    event = {
        "Records": [{
            "dynamodb": {
                "NewImage": {
                    "id": {"S": "1"},
                    "title": {"S": "Python 3.12 Released"},
                    "source": {"S": "reddit"},
                    "published_at": {"S": "2025-08-24T12:00:00Z"}
                }
            }
        }]
    }

    result = filter_lambda.lambda_handler(event, None, db_client=mock_client)

    assert result["processed"] == 1
    mock_client.put_item.assert_called_once()
