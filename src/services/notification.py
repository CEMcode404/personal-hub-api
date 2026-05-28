import os
import json

def send_sms(message: str):
    if os.environ.get("APP_ENV") == "local":
        print(f"[LOCAL SMS] {message}")
        return
    import boto3
    sns = boto3.client("sns")
    sns.publish(
        PhoneNumber=os.environ["NOTIFY_PHONE_NUMBER"],
        Message=message
    )

def send_websocket(payload: dict):
    if os.environ.get("APP_ENV") == "local":
        print(f"[LOCAL WS] {json.dumps(payload)}")
        return
    import boto3
    connection_id = _get_active_connection()
    if not connection_id:
        return
    client = boto3.client("apigatewaymanagementapi", endpoint_url=os.environ["WEBSOCKET_ENDPOINT"])
    client.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(payload).encode()
    )

def _get_active_connection():
    import boto3
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ.get("CONNECTIONS_TABLE", "personal-hub-connections"))
    result = table.scan(Limit=1)
    items = result.get("Items", [])
    return items[0]["connectionId"] if items else None