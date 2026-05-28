from src.db import get_table

TABLE = "personal-hub-content"

def find_all():
    result = get_table(TABLE).scan()
    return result["Items"]

def save(item: dict):
    get_table(TABLE).put_item(Item=item)