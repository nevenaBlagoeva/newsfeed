import unittest
import boto3
import json
from datetime import datetime, timezone

# Configuration — replace with your real deployed Lambda name and table
LAMBDA_NAME = "newsfeed-filter"
FILTERED_TABLE_NAME = "FilteredEvents"

lambda_client = boto3.client("lambda")
dynamodb = boto3.resource("dynamodb")
filtered_table = dynamodb.Table(FILTERED_TABLE_NAME)

class TestDeployedFilterLambda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_ids = []  # Track all inserted items for cleanup

    @classmethod
    def tearDownClass(cls):
        # Cleanup any test items inserted during tests
        for test_id in cls.test_ids:
            try:
                response = filtered_table.scan(
                    FilterExpression="id = :id",
                    ExpressionAttributeValues={":id": test_id}
                )
                for item in response.get("Items", []):
                    filtered_table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
                    print(f"Cleaned up filtered item: {item['id']}")
            except Exception as e:
                print(f"Failed to cleanup {test_id}: {e}")

    def _make_dynamodb_stream_record(self, item: dict):
        """Convert a normal dict into a DynamoDB stream-style NewImage"""
        def to_dynamodb_value(value):
            if isinstance(value, str):
                return {"S": value}
            elif isinstance(value, int) or isinstance(value, float):
                return {"N": str(value)}
            return {"S": str(value)}
        
        return {"dynamodb": {"NewImage": {k: to_dynamodb_value(v) for k, v in item.items()}}}

    def _invoke_lambda(self, event):
        """Invoke the deployed Lambda and parse the response"""
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        payload = response["Payload"].read()
        return json.loads(payload)

    def test_filter_lambda_success(self):
        """Test that a tech-related article is filtered"""
        test_id = f"e2e-filter-{int(datetime.now().timestamp())}"
        self.__class__.test_ids.append(test_id)

        raw_item = {
            "id": test_id,
            "source": "reddit",
            "title": "Python 3.12 Release Announcement",
            "body": "New features for Python developers",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "score": 500
        }

        event = {"Records": [self._make_dynamodb_stream_record(raw_item)]}
        result = self._invoke_lambda(event)

        self.assertEqual(result["processed"], 1)

        # Verify the item exists in the filtered table
        response = filtered_table.scan(
            FilterExpression="id = :id",
            ExpressionAttributeValues={":id": test_id}
        )
        items = response.get("Items", [])
        self.assertTrue(len(items) == 1)
        filtered_item = items[0]
        self.assertEqual(filtered_item["id"], test_id)
        self.assertIn("relevance_score", filtered_item)

    def test_filter_lambda_non_tech_skipped(self):
        """Test that a non-tech article is skipped"""
        test_id = f"e2e-filter-skip-{int(datetime.now().timestamp())}"
        self.__class__.test_ids.append(test_id)

        raw_item = {
            "id": test_id,
            "source": "reddit",
            "title": "Gardening Tips for Spring",
            "body": "How to plant tulips",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "score": 50
        }

        event = {"Records": [self._make_dynamodb_stream_record(raw_item)]}
        result = self._invoke_lambda(event)

        self.assertEqual(result["processed"], 0)

        # Verify no item exists in the filtered table
        response = filtered_table.scan(
            FilterExpression="id = :id",
            ExpressionAttributeValues={":id": test_id}
        )
        self.assertTrue(len(response.get("Items", [])) == 0)


if __name__ == "__main__":
    print("🧪 Running end-to-end tests against deployed Filter Lambda...")
    unittest.main()
