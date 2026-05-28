from src.db import get_table

TABLE = "personal-hub-connections"

def save(connection_id: str):
    get_table(TABLE).put_item(Item={"connectionId": connection_id})

def delete(connection_id: str):
    get_table(TABLE).delete_item(Key={"connectionId": connection_id})

def get_all():
    result = get_table(TABLE).scan()
    return [item["connectionId"] for item in result.get("Items", [])]