import uuid
from datetime import datetime, timezone
from src.repositories import wiki as wiki_repo
from src.schemas.wiki import CreateWikiRequest, UpdateWikiRequest
from src.models.wiki import Wiki

_INTERNAL_FIELDS = {"gsi_constant", "gsi_order_sk"}


def _clean(item: dict) -> dict:
    return {k: v for k, v in item.items() if k not in _INTERNAL_FIELDS}


def _compute_order_sk(is_pinned: bool, updated_at: str) -> str:
    return f"{1 if is_pinned else 0}#{updated_at}"


def list_all(limit: int = 10, cursor: dict = None, tag: str = None, category: str = None):
    result = wiki_repo.find_all(limit=limit, cursor=cursor, tag=tag, category=category)
    return {
        "items": [_clean(item) for item in result["items"]],
        "next_cursor": result["next_cursor"],
    }


def get_by_id(id: str):
    item = wiki_repo.find_by_id(id)
    if not item:
        raise ValueError("Wiki not found")
    return _clean(item)


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
        gsi_order_sk=_compute_order_sk(body.is_pinned, now),
    )
    wiki_repo.save(item)
    return _clean(item.__dict__)


def update(id: str, body: UpdateWikiRequest):
    existing = wiki_repo.find_by_id(id)
    if not existing:
        raise ValueError("Wiki not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}
    updates["updated_at"] = now

    is_pinned = updates.get("is_pinned", existing.get("is_pinned", False))
    updates["gsi_order_sk"] = _compute_order_sk(is_pinned, now)

    result = wiki_repo.update(id, updates)
    return _clean(result)


def delete(id: str):
    existing = wiki_repo.find_by_id(id)
    if not existing:
        raise ValueError("Wiki not found")
    wiki_repo.delete(id)