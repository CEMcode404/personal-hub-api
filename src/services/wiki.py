import uuid
from datetime import datetime, timezone
from repositories import wiki as wiki_repo
from schemas.wiki import CreateWikiRequest, UpdateWikiRequest
from models.wiki import Wiki
from utils.common import clean_internal_fields
from utils.media import (
    diff_image_keys,
    delete_media_keys,
    resolve_pending_images,
    apply_body_replacements,
    normalize_body_to_markers,
    resolve_body_markers_for_display,
    extract_image_keys_from_body,
)

_INTERNAL_FIELDS = {"gsi_constant", "gsi_order_sk"}


def _clean(item: dict) -> dict:
    return clean_internal_fields(item, _INTERNAL_FIELDS)


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
    cleaned = _clean(item)
    if cleaned.get("body"):
        cleaned["body"] = resolve_body_markers_for_display(cleaned["body"])
    return cleaned


def create(body: CreateWikiRequest):
    now = datetime.now(timezone.utc).isoformat()

    clean_images, upload_urls, body_replacements = resolve_pending_images(
        body.images, domain="wiki"
    )
    final_body = apply_body_replacements(body.body, body_replacements)

    item = Wiki(
        id=str(uuid.uuid4()),
        title=body.title,
        body=final_body,
        category=body.category,
        tags=body.tags,
        cover_image=body.cover_image,
        is_pinned=body.is_pinned,
        links=body.links,
        related=body.related,
        images=clean_images,
        created_at=now,
        updated_at=now,
        gsi_order_sk=_compute_order_sk(body.is_pinned, now),
    )
    wiki_repo.save(item)
    return {**_clean(item.__dict__), "upload_urls": upload_urls}


def update(id: str, body: UpdateWikiRequest):
    existing = wiki_repo.find_by_id(id)
    if not existing:
        raise ValueError("Wiki not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}

    upload_urls = {}
    if "images" in updates:
        pending_only = {
            k: v for k, v in updates["images"].items()
            if isinstance(v, dict) and "filename" in v
        }
        clean_new, upload_urls, body_replacements = resolve_pending_images(
            pending_only, domain="wiki"
        )
        if "body" in updates and body_replacements:
            updates["body"] = apply_body_replacements(updates["body"], body_replacements)
        del updates["images"]

    if "body" in updates:
        updates["body"] = normalize_body_to_markers(updates["body"])
        updates["images"] = {
            k: {} for k in extract_image_keys_from_body(updates["body"])
        }
        stale_keys = diff_image_keys(existing.get("images"), updates["images"])
        if stale_keys:
            delete_media_keys(stale_keys)

    updates["updated_at"] = now
    is_pinned = updates.get("is_pinned", existing.get("is_pinned", False))
    updates["gsi_order_sk"] = _compute_order_sk(is_pinned, now)

    result = wiki_repo.update(id, updates)
    return {**_clean(result), "upload_urls": upload_urls}


def delete(id: str):
    existing = wiki_repo.find_by_id(id)
    if not existing:
        raise ValueError("Wiki not found")

    existing_images = existing.get("images") or {}
    if existing_images:
        delete_media_keys(set(existing_images.keys()))

    wiki_repo.delete(id)