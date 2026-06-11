from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Attr
from src.db import get_table
from src.models.notification import Notification
from src.constants.notification import NotificationStatus

TABLE = "personal-hub-notifications"

def find_all(limit: int = 10, cursor: dict = None):
    kwargs = {"Limit": limit}
    if cursor:
        kwargs["ExclusiveStartKey"] = cursor
    result = get_table(TABLE).scan(**kwargs)
    return {
        "items": result.get("Items", []),
        "next_cursor": result.get("LastEvaluatedKey")
    }

def find_unread():
    result = get_table(TABLE).scan(
        FilterExpression=Attr("status").eq(NotificationStatus.unread.value)
    )
    return result.get("Items", [])

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