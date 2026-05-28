from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Content:
    id: str
    title: str
    slug: str
    body: str
    status: str
    type: str
    created_at: str
    updated_at: str
    excerpt: Optional[str] = None
    tags: list = field(default_factory=list)
    cover_image: Optional[str] = None
    published_at: Optional[str] = None