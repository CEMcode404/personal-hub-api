from pydantic import BaseModel
from typing import Optional

class CreateResearchRequest(BaseModel):
    title: str
    body: str
    category: Optional[str] = None
    tags: list[str] = []
    references: list[str] = []
    images: list[str] = []

class UpdateResearchRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    references: Optional[list[str]] = None
    images: Optional[list[str]] = None