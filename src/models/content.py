from dataclasses import dataclass, field
from typing import Optional
from constants.content import ContentType, ContentStatus

@dataclass
class Content:
    id: str
    title: str
    slug: str
    body: str
    status: ContentStatus
    type: ContentType
    created_at: str
    updated_at: str
    excerpt: Optional[str] = None
    tags: list = field(default_factory=list)
    cover_image: Optional[str] = None
    published_at: Optional[str] = None
    images: dict = field(default_factory=dict)
    # GSI: gsi_ordering — all content, latest-edited first
    gsi_constant: str = "CONTENT"
    # GSI: gsi_by_status — published_at if published, else updated_at
    gsi_status_sk: Optional[str] = None