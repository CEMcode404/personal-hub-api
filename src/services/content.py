import uuid
from datetime import datetime, timezone
from src.schemas.content import CreateContentRequest, UpdateContentRequest
from src.models.content import Content
from src.repositories import content as content_repo
from src.constants.content import ContentStatus
from src.utils.common import clean_internal_fields
from slugify import slugify

_INTERNAL_FIELDS = {"gsi_constant", "gsi_status_sk"}


def _clean(item: dict) -> dict:
    return clean_internal_fields(item, _INTERNAL_FIELDS)


def _compute_status_sk(status: str, updated_at: str, published_at: str = None) -> str:
    if status == ContentStatus.published.value and published_at:
        return published_at
    return updated_at


def list_all(limit: int = 10, cursor: dict = None, status: str = None, type: str = None):
    result = content_repo.find_all(limit=limit, cursor=cursor, status=status, type=type)
    return {
        "items": [_clean(item) for item in result["items"]],
        "next_cursor": result["next_cursor"],
    }


def get_by_id(id: str):
    item = content_repo.find_by_id(id)
    if not item:
        raise ValueError("Content not found")
    return _clean(item)


def get_by_slug(slug: str):
    item = content_repo.find_by_slug(slug)
    if not item:
        raise ValueError("Content not found")
    return _clean(item)


def _generate_unique_slug(title: str, exclude_id: str = None) -> str:
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while True:
        existing = content_repo.find_by_slug(slug)
        if not existing or (exclude_id and existing.get("id") == exclude_id):
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def create(body: CreateContentRequest):
    now = datetime.now(timezone.utc).isoformat()
    item = Content(
        id=str(uuid.uuid4()),
        title=body.title,
        slug=_generate_unique_slug(body.title),
        body=body.body,
        type=body.type,
        status=ContentStatus.draft,
        excerpt=body.excerpt,
        tags=body.tags,
        cover_image=body.cover_image,
        created_at=now,
        updated_at=now,
        gsi_status_sk=_compute_status_sk(ContentStatus.draft.value, now),
    )
    content_repo.save(item)
    return _clean(item.__dict__)


def update(id: str, body: UpdateContentRequest):
    existing = content_repo.find_by_id(id)
    if not existing:
        raise ValueError("Content not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}

    if "title" in updates:
        updates["slug"] = _generate_unique_slug(updates["title"], exclude_id=id)

    if updates.get("status") == ContentStatus.published.value:
        updates["published_at"] = now

    updates["updated_at"] = now

    status = updates.get("status", existing.get("status"))
    published_at = updates.get("published_at", existing.get("published_at"))
    updates["gsi_status_sk"] = _compute_status_sk(status, now, published_at)

    result = content_repo.update(id, updates)
    return _clean(result)


def delete(id: str):
    existing = content_repo.find_by_id(id)
    if not existing:
        raise ValueError("Content not found")
    content_repo.delete(id)