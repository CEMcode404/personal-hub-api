from dataclasses import dataclass, field
from typing import Optional
from src.constants.research import ResearchStatus


@dataclass
class Research:
    id: str
    title: str
    body: str
    status: ResearchStatus
    created_at: str
    updated_at: str
    category: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    published_at: Optional[str] = None