import uuid
from datetime import datetime, timezone
from repositories import research as research_repo
from schemas.research import CreateResearchRequest, UpdateResearchRequest
from models.research import Research
from constants.research import ResearchStatus
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

_INTERNAL_FIELDS = {"gsi_constant"}


def _clean(item: dict) -> dict:
    return clean_internal_fields(item, _INTERNAL_FIELDS)


def list_all(limit: int = 10, cursor: dict = None, category: str = None, status: str = None):
    result = research_repo.find_all(limit=limit, cursor=cursor, category=category, status=status)
    return {
        "items": [_clean(item) for item in result["items"]],
        "next_cursor": result["next_cursor"],
    }


def get_by_id(id: str):
    item = research_repo.find_by_id(id)
    if not item:
        raise ValueError("Research not found")
    cleaned = _clean(item)
    if cleaned.get("body"):
        cleaned["body"] = resolve_body_markers_for_display(cleaned["body"])
    # Defensively handle legacy list-shaped images from before the dict migration
    if isinstance(cleaned.get("images"), list):
        cleaned["images"] = {}
    return cleaned


def create(body: CreateResearchRequest):
    now = datetime.now(timezone.utc).isoformat()

    clean_images, upload_urls, body_replacements = resolve_pending_images(
        body.images, domain="research"
    )
    final_body = apply_body_replacements(body.body, body_replacements)

    item = Research(
        id=str(uuid.uuid4()),
        title=body.title,
        body=final_body,
        status=ResearchStatus.draft,
        category=body.category,
        tags=body.tags,
        references=body.references,
        images=clean_images,
        created_at=now,
        updated_at=now,
    )
    research_repo.save(item)
    return {**_clean(item.__dict__), "upload_urls": upload_urls}


def update(id: str, body: UpdateResearchRequest):
    existing = research_repo.find_by_id(id)
    if not existing:
        raise ValueError("Research not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}

    upload_urls = {}
    if "images" in updates:
        pending_only = {
            k: v for k, v in updates["images"].items()
            if isinstance(v, dict) and "filename" in v
        }
        clean_new, upload_urls, body_replacements = resolve_pending_images(
            pending_only, domain="research"
        )
        if "body" in updates and body_replacements:
            updates["body"] = apply_body_replacements(updates["body"], body_replacements)
        del updates["images"]

    if "body" in updates:
        updates["body"] = normalize_body_to_markers(updates["body"])
        updates["images"] = {
            k: {} for k in extract_image_keys_from_body(updates["body"])
        }
        # Defensively handle legacy list-shaped images
        existing_images = existing.get("images")
        if isinstance(existing_images, list):
            existing_images = {}
        stale_keys = diff_image_keys(existing_images, updates["images"])
        if stale_keys:
            delete_media_keys(stale_keys)

    updates["updated_at"] = now

    result = research_repo.update(id, updates)
    return {**_clean(result), "upload_urls": upload_urls}


def delete(id: str):
    existing = research_repo.find_by_id(id)
    if not existing:
        raise ValueError("Research not found")

    existing_images = existing.get("images") or {}
    if isinstance(existing_images, list):
        existing_images = {}
    if existing_images:
        delete_media_keys(set(existing_images.keys()))

    research_repo.delete(id)