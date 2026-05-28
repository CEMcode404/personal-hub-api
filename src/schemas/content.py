from pydantic import BaseModel
from typing import Optional

class CreateContentRequest(BaseModel):
    title: str
    body: str
    type: str = "article"
    excerpt: Optional[str] = None
    tags: list[str] = []
    cover_image: Optional[str] = None

class UpdateContentRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    excerpt: Optional[str] = None
    tags: Optional[list[str]] = None
    cover_image: Optional[str] = None