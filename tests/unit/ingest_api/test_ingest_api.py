import hashlib
import unittest
import boto3
import json
from datetime import datetime, timezone

# Configuration — replace with your real deployed Lambda name and table
LAMBDA_NAME = "newsfeed-ingest_api"
DYNAMO_TABLE_NAME = "RawEvents"

lambda_client = boto3.client("lambda")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMO_TABLE_NAME)

def generate_fingerprint(body_str):
    """Generate fingerprint from JSON string body"""
    body = json.loads(body_str) if isinstance(body_str, str) else body_str
    content = f"{body['title']}{body.get('published_at', '')}{body['source']}"
    return hashlib.md5(content.encode()).hexdigest()


class TestDeployedApiLambda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_ids = []  # Track all inserted items for cleanup

    @classmethod
    def tearDownClass(cls):
        # Cleanup any test items inserted during tests
        for test_id in cls.test_ids:
            try:
                table.delete_item(Key={"id": test_id})
                print(f"✅ Cleaned up item: {test_id}")
            except Exception as e:
                print(f"⚠️ Failed to cleanup {test_id}: {e}")

    def _invoke_lambda(self, payload):
        """Invoke the deployed Lambda and parse the response"""
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )
        resp_payload = response["Payload"].read()
        return json.loads(resp_payload)

    def test_api_lambda_success(self):
        """Test successful API ingestion of a valid event"""
        test_id = f"api-test-{int(datetime.now().timestamp())}"

        event_data = {
            "id": test_id,
            "source": "reddit",
            "title": "API Lambda Test Article",
            "body": "This is an end-to-end test of the API ingestion",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "url": f"https://reddit.com/{test_id}"
        }

        fingerprint = generate_fingerprint(json.dumps(event_data))
        self.__class__.test_ids.append(fingerprint)


        payload = {"body": json.dumps(event_data)}

        result = self._invoke_lambda(payload)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["processed"], 1)
        self.assertEqual(body["total"], 1)
        self.assertIsNone(body["errors"])

        # Verify item exists in DynamoDB
        response = table.get_item(Key={"id": fingerprint})
        self.assertIn("Item", response)
        self.assertEqual(response["Item"]["id"], fingerprint)

    def test_api_lambda_duplicate_handling(self):
        """Test duplicate detection"""
        test_id = f"api-dup-{int(datetime.now().timestamp())}"

        event_data = {
            "id": test_id,
            "source": "reddit",
            "title": "Duplicate Test Article",
            "body": "Duplicate check test",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "url": f"https://reddit.com/{test_id}"
        }

        fingerprint = generate_fingerprint(json.dumps(event_data))
        self.__class__.test_ids.append(fingerprint)

        payload = {"body": json.dumps(event_data)}

        # First invocation
        result1 = self._invoke_lambda(payload)
        self.assertEqual(json.loads(result1["body"])["processed"], 1)

        # Second invocation should skip duplicate
        result2 = self._invoke_lambda(payload)
        body2 = json.loads(result2["body"])
        self.assertEqual(body2["processed"], 0)  # Duplicate skipped

    def test_api_lambda_invalid_event(self):
        """Test handling of invalid event"""
        invalid_event = {
            "body": json.dumps({"title": "Missing required fields"})
        }
        result = self._invoke_lambda(invalid_event)
        body = json.loads(result["body"])
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(body["processed"], 0)
        self.assertEqual(body["total"], 1)
        self.assertIsNotNone(body["errors"])


if __name__ == "__main__":
    print("🧪 Running end-to-end tests against deployed API Lambda...")
    unittest.main()
