import uuid
from datetime import datetime, timezone
from schemas.content import CreateContentRequest, UpdateContentRequest
from models.content import Content
from repositories import content as content_repo
from constants.content import ContentStatus
from utils.common import clean_internal_fields
from utils.media import (
    diff_image_keys,
    delete_media_keys,
    resolve_pending_images,
    apply_body_replacements,
    promote_to_public,
    demote_to_private,
    rewrite_body_for_moved_images,
    resolve_body_markers_for_display,
    normalize_body_to_markers,
    extract_image_keys_from_body,
)
from slugify import slugify

_INTERNAL_FIELDS = {"gsi_constant", "gsi_status_sk"}


def _clean(item: dict) -> dict:
    return clean_internal_fields(item, _INTERNAL_FIELDS)


def _compute_status_sk(status: str, updated_at: str, published_at: str = None) -> str:
    if status == ContentStatus.published.value and published_at:
        return published_at
    return updated_at


def _is_publicly_visible(status: str) -> bool:
    return status == ContentStatus.published.value


def list_all(limit: int = 10, cursor: dict = None, status: str = None, type: str = None):
    result = content_repo.find_all(limit=limit, cursor=cursor, status=status, type=type)
    return {
        "items": [_clean(item) for item in result["items"]],
        "next_cursor": result["next_cursor"],
    }


def get_by_id(id: str):
    """Admin-only read. Resolves any private-image markers in body into
    fresh, working presigned URLs for this view."""
    item = content_repo.find_by_id(id)
    if not item:
        raise ValueError("Content not found")
    cleaned = _clean(item)
    if cleaned.get("body"):
        cleaned["body"] = resolve_body_markers_for_display(cleaned["body"])
    return cleaned


def get_by_slug(slug: str):
    """Public read. Resolves markers — published content"""
    item = content_repo.find_by_slug(slug)
    if not item:
        raise ValueError("Content not found")
    cleaned = _clean(item)
    if cleaned.get("body"):
        cleaned["body"] = resolve_body_markers_for_display(cleaned["body"])
    return cleaned


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

    clean_images, upload_urls, body_replacements = resolve_pending_images(body.images)
    final_body = apply_body_replacements(body.body, body_replacements)

    item = Content(
        id=str(uuid.uuid4()),
        title=body.title,
        slug=_generate_unique_slug(body.title),
        body=final_body,
        type=body.type,
        status=ContentStatus.draft,
        excerpt=body.excerpt,
        tags=body.tags,
        cover_image=body.cover_image,
        images=clean_images,
        created_at=now,
        updated_at=now,
        gsi_status_sk=_compute_status_sk(ContentStatus.draft.value, now),
    )
    content_repo.save(item)
    return {**_clean(item.__dict__), "upload_urls": upload_urls}


def update(id: str, body: UpdateContentRequest):
    existing = content_repo.find_by_id(id)
    if not existing:
        raise ValueError("Content not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}

    if "title" in updates:
        if not existing.get("published_at"):
            updates["slug"] = _generate_unique_slug(updates["title"], exclude_id=id)

    if updates.get("status") == ContentStatus.published.value:
        updates["published_at"] = now

    upload_urls = {}
    if "images" in updates:
        # Only entries with 'filename' are meaningful here — they're
        # the new uploads this call. Everything else in the submitted
        # images dict is ignored; "what's currently in use" is derived
        # from body itself below, not trusted from the client.
        pending_only = {
            k: v for k, v in updates["images"].items()
            if isinstance(v, dict) and "filename" in v
        }
        clean_new, upload_urls, body_replacements = resolve_pending_images(pending_only)
        if "body" in updates and body_replacements:
            updates["body"] = apply_body_replacements(updates["body"], body_replacements)
        del updates["images"]  # rebuilt below from body, after normalization

    if "body" in updates:
        updates["body"] = normalize_body_to_markers(updates["body"])
        updates["images"] = {
            k: {} for k in extract_image_keys_from_body(updates["body"])
        }
        stale_keys = diff_image_keys(existing.get("images"), updates["images"])
        if stale_keys:
            delete_media_keys(stale_keys)

    if "status" in updates:
        old_visible = _is_publicly_visible(existing.get("status"))
        new_visible = _is_publicly_visible(updates["status"])
        current_images = updates.get("images", existing.get("images", {}))
        image_keys = set(current_images.keys())

        moved = {}
        if not old_visible and new_visible:
            moved = promote_to_public(image_keys)
        elif old_visible and not new_visible:
            moved = demote_to_private(image_keys)

        if moved:
            updates["images"] = {moved.get(k, k): v for k, v in current_images.items()}
            body_to_rewrite = updates.get("body", existing.get("body", ""))
            updates["body"] = rewrite_body_for_moved_images(body_to_rewrite, moved)

    updates["updated_at"] = now

    status = updates.get("status", existing.get("status"))
    published_at = updates.get("published_at", existing.get("published_at"))
    updates["gsi_status_sk"] = _compute_status_sk(status, now, published_at)

    result = content_repo.update(id, updates)
    return {**_clean(result), "upload_urls": upload_urls}


def delete(id: str):
    existing = content_repo.find_by_id(id)
    if not existing:
        raise ValueError("Content not found")

    existing_images = existing.get("images") or {}
    if existing_images:
        delete_media_keys(set(existing_images.keys()))

    content_repo.delete(id)