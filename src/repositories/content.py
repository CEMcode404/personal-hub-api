from src.db import get_table
from dataclasses import asdict
from src.models.content import Content

TABLE = "personal-hub-content"

def find_all(limit: int = 10, cursor: dict = None, slug: str = None):
    kwargs = {"Limit": limit}
    if cursor:
        kwargs["ExclusiveStartKey"] = cursor
    if slug:
        kwargs["FilterExpression"] = "slug = :slug"
        kwargs["ExpressionAttributeValues"] = {":slug": slug}
    result = get_table(TABLE).scan(**kwargs)
    return {
        "items": result.get("Items", []),
        "next_cursor": result.get("LastEvaluatedKey")
    }

def find_by_id(id: str):
    result = get_table(TABLE).get_item(Key={"id": id})
    return result.get("Item")

def find_by_slug(slug: str):
    # NOTE: uses scan which reads the entire table — fine for small datasets.
    # For production at scale, add a GSI on `slug` in DynamoDB
    # and replace this with a query() call for better performance.
    result = get_table(TABLE).scan(
        FilterExpression="slug = :slug",
        ExpressionAttributeValues={":slug": slug},
        Limit=1
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
        ReturnValues="ALL_NEW"
    )
    return result.get("Attributes")

def delete(id: str):
    get_table(TABLE).delete_item(Key={"id": id})