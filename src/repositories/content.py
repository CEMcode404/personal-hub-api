import json
from dataclasses import asdict
from boto3.dynamodb.conditions import Key, Attr
from src.db import get_table
from src.models.content import Content

TABLE = "personal-hub-content"


def find_all(limit: int = 10, cursor: dict = None, status: str = None, type: str = None):
    table = get_table(TABLE)
    kwargs = {"Limit": limit + 1, "ScanIndexForward": False}

    if cursor:
        kwargs["ExclusiveStartKey"] = cursor

    if status:
        kwargs["IndexName"] = "gsi_by_status"
        kwargs["KeyConditionExpression"] = Key("status").eq(status)
    else:
        kwargs["IndexName"] = "gsi_ordering"
        kwargs["KeyConditionExpression"] = Key("gsi_constant").eq("CONTENT")

    if type:
        kwargs["FilterExpression"] = Attr("type").eq(type)

    result = table.query(**kwargs)
    items = result.get("Items", [])

    has_more = len(items) > limit
    page_items = items[:limit]

    next_cursor = None
    if has_more:
        last_shown = items[limit - 1]
        if status:
            next_cursor = {
                "id": last_shown["id"],
                "status": last_shown["status"],
                "gsi_status_sk": last_shown["gsi_status_sk"],
            }
        else:
            next_cursor = {
                "id": last_shown["id"],
                "gsi_constant": last_shown["gsi_constant"],
                "updated_at": last_shown["updated_at"],
            }

    return {
        "items": page_items,
        "next_cursor": json.dumps(next_cursor) if next_cursor else None,
    }


def find_by_id(id: str):
    result = get_table(TABLE).get_item(Key={"id": id})
    return result.get("Item")


def find_by_slug(slug: str):
    table = get_table(TABLE)
    result = table.query(
        IndexName="gsi_by_slug",
        KeyConditionExpression=Key("slug").eq(slug),
        Limit=1,
    )
    items = result.get("Items", [])
    return items[0] if items else None


def save(item: Content):
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