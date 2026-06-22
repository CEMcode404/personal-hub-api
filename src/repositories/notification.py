import json
from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key
from db import get_table
from models.notification import Notification
from constants.notification import NotificationStatus

TABLE = "personal-hub-notifications"

def find_all(limit: int = 10, cursor: dict = None):
    kwargs = {"Limit": limit + 1}
    if cursor:
        kwargs["ExclusiveStartKey"] = cursor
    result = get_table(TABLE).scan(**kwargs)
    items = result.get("Items", [])

    has_more = len(items) > limit
    page_items = items[:limit]

    next_cursor = None
    if has_more:
        last = page_items[-1]
        next_cursor = {"id": last["id"]}

    return {
        "items": page_items,
        "next_cursor": json.dumps(next_cursor) if next_cursor else None,
    }

def find_unread(limit: int = 10, cursor: dict = None):
    kwargs = {
        "IndexName": "gsi_by_status",
        "KeyConditionExpression": Key("status").eq(NotificationStatus.unread.value),
        "Limit": limit + 1,
        "ScanIndexForward": False,
    }
    if cursor:
        kwargs["ExclusiveStartKey"] = cursor
    result = get_table(TABLE).query(**kwargs)
    items = result.get("Items", [])

    has_more = len(items) > limit
    page_items = items[:limit]

    next_cursor = None
    if has_more:
        last = page_items[-1]
        next_cursor = {"id": last["id"], "status": last["status"], "created_at": last["created_at"]}

    return {
        "items": page_items,
        "next_cursor": json.dumps(next_cursor) if next_cursor else None,
    }

def save(item: Notification):
    data = {k: v for k, v in asdict(item).items() if v is not None}
    get_table(TABLE).put_item(Item=data)

def mark_as_read(id: str) -> dict:
    ttl = int((datetime.now(timezone.utc) + timedelta(days=60)).timestamp())
    result = get_table(TABLE).update_item(
        Key={"id": id},
        UpdateExpression="SET #status = :status, #ttl = :ttl",
        ExpressionAttributeNames={"#status": "status", "#ttl": "ttl"},
        ExpressionAttributeValues={":status": NotificationStatus.read.value, ":ttl": ttl},
        ReturnValues="ALL_NEW"
    )
    return result.get("Attributes")