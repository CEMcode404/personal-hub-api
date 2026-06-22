from dataclasses import dataclass, field
from typing import Optional
from constants.research import ResearchStatus


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
    images: dict = field(default_factory=dict)
    # GSI: gsi_ordering — all research items, latest-updated first
    gsi_constant: str = "RESEARCH"