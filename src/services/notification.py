import os
import json
import uuid
from datetime import datetime, timezone
from src.repositories import notification as notification_repo
from src.repositories import connection as connection_repo
from src.models.notification import Notification
import boto3

def send_sms(message: str):
    if os.environ.get("APP_ENV") == "local":
        print(f"[LOCAL SMS] {message}")
        return
    sns = boto3.client("sns")
    sns.publish(
        PhoneNumber=os.environ["NOTIFY_PHONE_NUMBER"],
        Message=message
    )

def send_websocket(payload: dict):
    if os.environ.get("APP_ENV") == "local":
        print(f"[LOCAL WS] {json.dumps(payload)}")
        return
    connection_ids = connection_repo.get_all()
    client = boto3.client("apigatewaymanagementapi", endpoint_url=os.environ["WEBSOCKET_ENDPOINT"])
    for connection_id in connection_ids:
        try:
            client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(payload).encode()
            )
        except client.exceptions.GoneException:
            connection_repo.delete(connection_id)

def create_notification(todo: dict, message: str):
    now = datetime.now(timezone.utc).isoformat()
    item = Notification(
        id=str(uuid.uuid4()),
        title=todo["title"],
        message=message,
        status="unread",
        todo_id=todo["id"],
        created_at=now,
    )
    notification_repo.save(item)
    return item

def notify(todo: dict):
    message = f"Todo reminder: {todo['title']}"
    if todo.get("notify_sms"):
        send_sms(message)
    if todo.get("notify_web"):
        notification = create_notification(todo, message)
        send_websocket({"type": "todo_reminder", "notification": notification.__dict__})
    else:
        create_notification(todo, message)