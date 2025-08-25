import os
import boto3
from typing import Dict, Any

class DynamoDBClient:
    def __init__(self, table_name: str = None):
        self.table_name = table_name or os.getenv("FILTERED_TABLE_NAME", "FilteredEvents")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def put_item(self, item: Dict[str, Any]):
        self.table.put_item(Item=item)

    def get_item_by_id(self, item_id: str):
        response = self.table.scan(
            FilterExpression="id = :id",
            ExpressionAttributeValues={":id": item_id}
        )
        return response.get("Items", [])

    @staticmethod
    def dynamodb_to_dict(dynamodb_item: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for k, v in dynamodb_item.items():
            if "S" in v:
                result[k] = v["S"]
            elif "N" in v:
                result[k] = int(v["N"]) if v["N"].isdigit() else float(v["N"])
        return result
