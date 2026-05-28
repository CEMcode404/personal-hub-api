import uuid
from datetime import datetime, timezone
from src.schemas.content import CreateContentRequest
from src.models.content import Content
from src.repositories import content as content_repo
from slugify import slugify

def list_all():
    return content_repo.find_all()

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