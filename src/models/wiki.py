from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Wiki:
    id: str
    title: str
    body: str
    created_at: str
    updated_at: str
    category: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    cover_image: Optional[str] = None
    is_pinned: bool = False
    links: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)
    # GSI: gsi_ordering — all wiki items, pinned-first then by updated_at
    gsi_constant: str = "WIKI"
    gsi_order_sk: Optional[str] = None