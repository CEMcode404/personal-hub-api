import os
import json
import uuid
from datetime import datetime, timezone
from repositories import notification as notification_repo
from repositories import connection as connection_repo
from models.notification import Notification
from constants.notification import NotificationStatus
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


def create_notification(todo: dict, message: str) -> Notification:
    now = datetime.now(timezone.utc).isoformat()
    item = Notification(
        id=str(uuid.uuid4()),
        title=todo.get("title", "Untitled"),
        message=message,
        status=NotificationStatus.unread,
        todo_id=todo.get("id", ""),
        created_at=now,
    )
    notification_repo.save(item)
    return item


def notify(todo: dict):
    message = f"Todo reminder: {todo.get('title', 'Untitled')}"
    if todo.get("notify_sms"):
        try:
            send_sms(message)
        except Exception as e:
            print(f"[WARN] SMS failed for todo {todo.get('id')}: {e}")
    if todo.get("notify_web"):
        try:
            notification = create_notification(todo, message)
            send_websocket({"type": "todo_reminder", "notification": notification.__dict__})
        except Exception as e:
            print(f"[WARN] Web notification failed for todo {todo.get('id')}: {e}")