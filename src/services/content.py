import uuid
from datetime import datetime, timezone
from src.schemas.content import CreateContentRequest, UpdateContentRequest
from src.models.content import Content
from src.repositories import content as content_repo
from src.constants.content import ContentStatus
from slugify import slugify


def list_all(limit: int = 10, cursor: dict = None, slug: str = None):
    return content_repo.find_all(limit=limit, cursor=cursor, slug=slug)


def get_by_id(id: str):
    item = content_repo.find_by_id(id)
    if not item:
        raise ValueError("Content not found")
    return item


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
    )
    content_repo.save(item)
    return item


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
    return content_repo.update(id, updates)


def delete(id: str):
    existing = content_repo.find_by_id(id)
    if not existing:
        raise ValueError("Content not found")
    content_repo.delete(id)