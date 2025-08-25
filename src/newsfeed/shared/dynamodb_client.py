import boto3

class DynamoDBClient:
    def __init__(self, table_name: str):
        self.table = boto3.resource("dynamodb").Table(table_name)

    def put_item(self, item: dict):
        self.table.put_item(Item=item)

    def get_item(self, key: dict):
        return self.table.get_item(Key=key)

    def query(self, **kwargs):
        return self.table.query(**kwargs)

    def event_exists(self, fingerprint: str) -> bool:
        response = self.get_item({"id": fingerprint})
        return "Item" in response
