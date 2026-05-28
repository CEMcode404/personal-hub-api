import uuid
from datetime import datetime, timezone
from src.schemas.content import CreateContentRequest, UpdateContentRequest
from src.models.content import Content
from src.repositories import content as content_repo
from slugify import slugify

def list_all(limit: int = 10, cursor: dict = None, slug: str = None):
    return content_repo.find_all(limit=limit, cursor=cursor, slug=slug)

def get_by_id(id: str):
    item = content_repo.find_by_id(id)
    if not item:
        raise ValueError("Content not found")
    return item

def create(body: CreateContentRequest):
    now = datetime.now(timezone.utc).isoformat()
    item = Content(
        id=str(uuid.uuid4()),
        title=body.title,
        slug=slugify(body.title),
        body=body.body,
        type=body.type,
        status="draft",
        excerpt=body.excerpt,
        tags=body.tags,
        cover_image=body.cover_image,
        created_at=now,
        updated_at=now,
    )
    content_repo.save(item)
    return item

def update(id: str, body: UpdateContentRequest):
    existing = content_repo.find_by_id(id)
    if not existing:
        raise ValueError("Content not found")
    
    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    
    if "title" in updates:
        updates["slug"] = slugify(updates["title"])
    
    updates["updated_at"] = now
    content_repo.update(id, updates)
    return {**existing, **updates}

def delete(id: str):
    existing = content_repo.find_by_id(id)
    if not existing:
        raise ValueError("Content not found")
    content_repo.delete(id)