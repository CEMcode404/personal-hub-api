import json
from dataclasses import asdict
from boto3.dynamodb.conditions import Key
from src.db import get_table
from src.models.research import Research

TABLE = "personal-hub-research"


def find_all(limit: int = 10, cursor: dict = None, category: str = None, status: str = None):
    table = get_table(TABLE)
    kwargs = {"Limit": limit + 1, "ScanIndexForward": False}

    if cursor:
        kwargs["ExclusiveStartKey"] = cursor

    if category:
        kwargs["IndexName"] = "gsi_by_category"
        kwargs["KeyConditionExpression"] = Key("category").eq(category)
    elif status:
        kwargs["IndexName"] = "gsi_by_status"
        kwargs["KeyConditionExpression"] = Key("status").eq(status)
    else:
        kwargs["IndexName"] = "gsi_ordering"
        kwargs["KeyConditionExpression"] = Key("gsi_constant").eq("RESEARCH")

    result = table.query(**kwargs)
    items = result.get("Items", [])

    has_more = len(items) > limit
    page_items = items[:limit]

    next_cursor = None
    if has_more:
        last_shown = items[limit - 1]
        next_cursor = {"id": last_shown["id"], "updated_at": last_shown["updated_at"]}
        if category:
            next_cursor["category"] = last_shown["category"]
        elif status:
            next_cursor["status"] = last_shown["status"]
        else:
            next_cursor["gsi_constant"] = last_shown["gsi_constant"]

    return {
        "items": page_items,
        "next_cursor": json.dumps(next_cursor) if next_cursor else None,
    }


def find_by_id(id: str):
    result = get_table(TABLE).get_item(Key={"id": id})
    return result.get("Item")


def save(item: Research):
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
        ReturnValues="ALL_NEW",
    )
    return result.get("Attributes")


def delete(id: str):
    get_table(TABLE).delete_item(Key={"id": id})