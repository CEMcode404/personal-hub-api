from dataclasses import asdict
from boto3.dynamodb.conditions import Attr
from src.db import get_table
from src.models.todo import Todo

TABLE = "personal-hub-todos"

def find_all(limit: int = 10, cursor: dict = None):
    kwargs = {
        "Limit": limit,
        "FilterExpression": ~(Attr("is_recurring").eq(True) & Attr("recurring_parent_id").not_exists()),
    }
    if cursor:
        kwargs["ExclusiveStartKey"] = cursor
    result = get_table(TABLE).scan(**kwargs)
    return {
        "items": result.get("Items", []),
        "next_cursor": result.get("LastEvaluatedKey")
    }

def find_by_id(id: str):
    result = get_table(TABLE).get_item(Key={"id": id})
    return result.get("Item")

def save(item: Todo):
    data = {k: v for k, v in asdict(item).items() if v is not None}
    get_table(TABLE).put_item(Item=data)

def update(id: str, updates: dict) -> dict:
    expression = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
    attr_names = {f"#{k}": k for k in updates}
    attr_values = {f":{k}": v for k, v in updates.items()}
    result = get_table(TABLE).update_item(
        Key={"id": id},
        UpdateExpression=expression,
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
        ReturnValues="ALL_NEW"
    )
    return result.get("Attributes")

def delete(id: str):
    get_table(TABLE).delete_item(Key={"id": id})