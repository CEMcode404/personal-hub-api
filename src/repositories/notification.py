from dataclasses import asdict
from src.db import get_table
from src.models.notification import Notification

TABLE = "personal-hub-notifications"

def find_all():
    result = get_table(TABLE).scan()
    return result.get("Items", [])

def find_unread():
    from boto3.dynamodb.conditions import Attr
    result = get_table(TABLE).scan(
        FilterExpression=Attr("status").eq("unread")
    )
    return result.get("Items", [])

def save(item: Notification):
    data = {k: v for k, v in asdict(item).items() if v is not None}
    get_table(TABLE).put_item(Item=data)

def mark_as_read(id: str):
    from datetime import datetime, timezone, timedelta
    ttl = int((datetime.now(timezone.utc) + timedelta(days=60)).timestamp())
    get_table(TABLE).update_item(
        Key={"id": id},
        UpdateExpression="SET #status = :status, #ttl = :ttl",
        ExpressionAttributeNames={"#status": "status", "#ttl": "ttl"},
        ExpressionAttributeValues={":status": "read", ":ttl": ttl}
    )