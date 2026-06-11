import uuid
from datetime import datetime, timezone
from src.repositories import wiki as wiki_repo
from src.schemas.wiki import CreateWikiRequest, UpdateWikiRequest
from src.models.wiki import Wiki


def list_all(limit: int = 10, cursor: dict = None, tag: str = None, category: str = None):
    return wiki_repo.find_all(limit=limit, cursor=cursor, tag=tag, category=category)


def get_by_id(id: str):
    item = wiki_repo.find_by_id(id)
    if not item:
        raise ValueError("Wiki not found")
    return item


def create(body: CreateWikiRequest):
    now = datetime.now(timezone.utc).isoformat()
    item = Wiki(
        id=str(uuid.uuid4()),
        title=body.title,
        body=body.body,
        category=body.category,
        tags=body.tags,
        cover_image=body.cover_image,
        is_pinned=body.is_pinned,
        links=body.links,
        related=body.related,
        created_at=now,
        updated_at=now,
    )
    wiki_repo.save(item)
    return item


def update(id: str, body: UpdateWikiRequest):
    existing = wiki_repo.find_by_id(id)
    if not existing:
        raise ValueError("Wiki not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}
    updates["updated_at"] = now
    return wiki_repo.update(id, updates)


def delete(id: str):
    existing = wiki_repo.find_by_id(id)
    if not existing:
        raise ValueError("Wiki not found")
    wiki_repo.delete(id)