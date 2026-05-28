from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Research:
    id: str
    title: str
    body: str
    status: str
    created_at: str
    updated_at: str
    category: Optional[str] = None
    tags: list = field(default_factory=list)
    references: list = field(default_factory=list)
    images: list = field(default_factory=list)