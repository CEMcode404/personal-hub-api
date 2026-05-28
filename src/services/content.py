import uuid
from datetime import datetime, timezone
from src.repositories import content as content_repo

def list_all():
    return content_repo.find_all()

def create(body: dict):
    if not body.get("title"):
        raise ValueError("title is required")
    
    item = {
        "id": str(uuid.uuid4()),
        "title": body.get("title"),
        "body": body.get("body"),
        "type": body.get("type", "article"),
        "status": "draft",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    content_repo.save(item)
    return item