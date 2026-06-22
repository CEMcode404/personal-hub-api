import json
from dataclasses import asdict
from boto3.dynamodb.conditions import Key, Attr
from db import get_table
from models.todo import Todo
from constants.todo import TodoParent

TABLE = "personal-hub-todos"


def find_all(limit: int = 10, cursor: dict = None, parent: str = TodoParent.standalone.value, status: str = None):
    table = get_table(TABLE)
    kwargs = {"Limit": limit + 1, "ScanIndexForward": False}

    if cursor:
        kwargs["ExclusiveStartKey"] = cursor

    if status and not parent:
        kwargs["IndexName"] = "gsi_by_status"
        kwargs["KeyConditionExpression"] = Key("status").eq(status)
    else:
        kwargs["IndexName"] = "gsi_by_parent"
        kwargs["KeyConditionExpression"] = Key("recurring_parent_id").eq(parent)
        if status:
            kwargs["FilterExpression"] = Attr("status").eq(status)

    result = table.query(**kwargs)
    items = result.get("Items", [])

    has_more = len(items) > limit
    page_items = items[:limit]

    next_cursor = None
    if has_more:
        last_shown = items[limit - 1]
        if status and not parent:
            next_cursor = {"id": last_shown["id"], "status": last_shown["status"], "updated_at": last_shown["updated_at"]}
        else:
            next_cursor = {"id": last_shown["id"], "recurring_parent_id": last_shown["recurring_parent_id"], "gsi_order_sk": last_shown["gsi_order_sk"]}

    return {
        "items": page_items,
        "next_cursor": json.dumps(next_cursor) if next_cursor else None,
    }


def find_by_id(id: str):
    result = get_table(TABLE).get_item(Key={"id": id})
    return result.get("Item")

def has_children(id: str) -> bool:
    result = get_table(TABLE).query(
        IndexName="gsi_by_parent",
        KeyConditionExpression=Key("recurring_parent_id").eq(id),
        Limit=1,
    )
    return len(result.get("Items", [])) > 0


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