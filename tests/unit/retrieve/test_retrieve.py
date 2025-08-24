import unittest
import boto3
import json

# Replace with your deployed Lambda name
LAMBDA_NAME = "newsfeed-retrieve"
FILTERED_TABLE_NAME = "FilteredNews"

lambda_client = boto3.client("lambda")
dynamodb = boto3.resource("dynamodb")
filtered_table = dynamodb.Table(FILTERED_TABLE_NAME)

class TestRetrieveFilteredLambda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Optionally track test items if you want to insert test data
        cls.test_ids = []

    def _invoke_lambda(self, payload):
        """Invoke deployed Lambda and return parsed JSON response"""
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )
        resp_payload = response["Payload"].read()
        return json.loads(resp_payload)

    def test_retrieve_filtered_basic(self):
        """Test retrieving filtered events without dashboard metadata"""
        payload = {"queryStringParameters": {"limit": "10"}}
        result = self._invoke_lambda(payload)

        # Check statusCode
        self.assertEqual(result["statusCode"], 200)

        # Parse events
        events = json.loads(result["body"])
        self.assertIsInstance(events, list)
        self.assertLessEqual(len(events), 10)

        if events:
            # Verify basic fields exist
            event = events[0]
            self.assertIn("id", event)
            self.assertIn("title", event)
            self.assertIn("source", event)
            self.assertIn("body", event)
            self.assertIn("published_at", event)
            self.assertIn("url", event)
            # Metadata fields should NOT exist
            self.assertNotIn("SK", event)
            self.assertNotIn("relevance_score", event)

    def test_retrieve_filtered_dashboard(self):
        """Test retrieving filtered events with dashboard metadata"""
        payload = {"queryStringParameters": {"limit": "5", "dashboard": "true"}}
        result = self._invoke_lambda(payload)
        self.assertEqual(result["statusCode"], 200)

        events = json.loads(result["body"])
        self.assertIsInstance(events, list)
        self.assertLessEqual(len(events), 5)

        if events:
            event = events[0]
            # Metadata fields should exist
            self.assertIn("SK", event)
            self.assertIn("relevance_score", event)
            self.assertIsInstance(event["relevance_score"], float)

    def test_retrieve_filtered_debug(self):
        """Test retrieving filtered events with debug flag"""
        payload = {"queryStringParameters": {"debug": "true", "limit": "3"}}
        result = self._invoke_lambda(payload)
        self.assertEqual(result["statusCode"], 200)

        events = json.loads(result["body"])
        self.assertIsInstance(events, list)
        self.assertLessEqual(len(events), 3)

        if events:
            event = events[0]
            self.assertIn("SK", event)
            self.assertIn("relevance_score", event)

if __name__ == "__main__":
    print("🧪 Running end-to-end tests against deployed retrieve-filtered Lambda...")
    unittest.main()
