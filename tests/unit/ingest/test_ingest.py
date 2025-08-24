import hashlib
import boto3
import json
import unittest
from datetime import datetime, timezone

# Configuration
LAMBDA_NAME = "newsfeed-ingest"
RAW_DYNAMO_TABLE = "RawEvents"
FILTERED_DYNAMO_TABLE = "FilteredEvents"

lambda_client = boto3.client("lambda")
dynamodb = boto3.resource("dynamodb")
tableRaw = dynamodb.Table(RAW_DYNAMO_TABLE)
tableFiltered = dynamodb.Table(FILTERED_DYNAMO_TABLE)

def generate_fingerprint(body_str):
    """Generate fingerprint from JSON string body"""
    body = json.loads(body_str) if isinstance(body_str, str) else body_str
    content = f"{body['title']}{body.get('published_at', '')}{body['source']}"
    return hashlib.md5(content.encode()).hexdigest()

class TestDeployedLambda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table_keys = []  # Track all inserted items across all tests

    @classmethod
    def tearDownClass(cls):
        # Cleanup all test items even if tests fail
        for key in cls.table_keys:
            try:
                # The Lambda uses fingerprint as the actual key, not the original ID
                fingerprint = generate_fingerprint(json.dumps({
                    "id": key,
                    "source": "reddit", 
                    "title": "Test Article",  # This won't match but we need something
                    "published_at": ""
                }))
                
                # Try deleting with fingerprint as key
                tableRaw.delete_item(Key={"id": fingerprint})
                print(f"Cleaned up test item: {fingerprint}")
            except Exception as e:
                print(f"Failed to clean up {key}: {e}")

    def _invoke_lambda(self, event):
        """Helper to invoke the deployed Lambda and parse the response"""
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(event),
        )
        payload = response["Payload"].read()
        return json.loads(payload)

    def test_lambda_success(self):
        """Test sending a valid SQS message"""
        test_id = f"e2e-test-{int(datetime.now().timestamp())}"

        article_data = {
            "id": test_id,
            "source": "reddit",
            "title": "E2E Test Article",
            "body": "This is an end-to-end test",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "url": f"https://reddit.com/{test_id}"
        }

        event = {
            "Records": [{
                "body": json.dumps(article_data)
            }]
        }

        # Track the fingerprint that will be used as the actual key
        fingerprint = generate_fingerprint(json.dumps(article_data))
        self.__class__.table_keys.append(fingerprint)

        result = self._invoke_lambda(event)
        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["skipped"], 0)

    def test_lambda_duplicate_handling(self):
        """Test duplicate message detection"""
        test_id = f"e2e-dup-{int(datetime.now().timestamp())}"

        article = {
            "id": test_id,
            "source": "reddit",
            "title": "Duplicate Test Article",
            "body": "Same content",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "url": f"https://reddit.com/{test_id}"
        }

        event = {"Records": [{"body": json.dumps(article)}, {"body": json.dumps(article)}]}

        # Track the fingerprint that will be used as the actual key
        fingerprint = generate_fingerprint(json.dumps(article))
        self.__class__.table_keys.append(fingerprint)

        result = self._invoke_lambda(event)
        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["skipped"], 1)


if __name__ == "__main__":
    print("🧪 Running end-to-end tests against deployed Lambda...")
    unittest.main()
