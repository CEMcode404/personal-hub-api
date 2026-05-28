from pydantic import BaseModel
from typing import Optional

class CreateContentRequest(BaseModel):
    title: str
    body: str
    type: str = "article"
    excerpt: Optional[str] = None
    tags: list[str] = []
    cover_image: Optional[str] = None