import uuid
from datetime import datetime, timezone
from src.repositories import research as research_repo
from src.schemas.research import CreateResearchRequest, UpdateResearchRequest
from src.models.research import Research
from src.constants.research import ResearchStatus
from src.utils.common import clean_internal_fields

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
    return _clean(item)


def create(body: CreateResearchRequest):
    now = datetime.now(timezone.utc).isoformat()
    item = Research(
        id=str(uuid.uuid4()),
        title=body.title,
        body=body.body,
        status=ResearchStatus.draft,
        category=body.category,
        tags=body.tags,
        references=body.references,
        images=body.images,
        created_at=now,
        updated_at=now,
    )
    research_repo.save(item)
    return _clean(item.__dict__)


def update(id: str, body: UpdateResearchRequest):
    existing = research_repo.find_by_id(id)
    if not existing:
        raise ValueError("Research not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}
    updates["updated_at"] = now

    result = research_repo.update(id, updates)
    return _clean(result)


def delete(id: str):
    existing = research_repo.find_by_id(id)
    if not existing:
        raise ValueError("Research not found")
    research_repo.delete(id)