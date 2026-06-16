import re
import nh3
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from src.constants.research import ResearchStatus
from src.constants.common import  ALLOWED_TAGS, ALLOWED_ATTRIBUTES

BODY_CLEANER = nh3.Cleaner(
    tags=ALLOWED_TAGS,
    attributes=ALLOWED_ATTRIBUTES,
    url_schemes={"http", "https", "mailto"},
    link_rel="noopener noreferrer",
    filter_style_properties={"width", "text-align", "color", "background-color"},
)

class ResearchValidatorMixin(BaseModel):
    @field_validator("title", mode="before", check_fields=False)
    @classmethod
    def sanitize_plain(cls, v):
        if v is None:
            return v
        return nh3.clean(v, tags=set()).strip()

    @field_validator("category", mode="before", check_fields=False)
    @classmethod
    def sanitize_category(cls, v):
        if v is None:
            return v
        return nh3.clean(v, tags=set()).strip() or None

    @field_validator("body", mode="before", check_fields=False)
    @classmethod
    def sanitize_body(cls, v):
        if v is None:
            return v
        return BODY_CLEANER.clean(v)

    @field_validator("tags", mode="before", check_fields=False)
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return v
        sanitized = [nh3.clean(tag, tags=set()).lower().strip() for tag in v]
        for tag in sanitized:
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds 50 characters")
            if not re.match(r"^[\w\-]+$", tag):
                raise ValueError(f"Tag '{tag}' contains invalid characters")
        return sanitized

    @field_validator("references", "images", mode="before", check_fields=False)
    @classmethod
    def validate_urls(cls, v):
        if v is None:
            return v
        for url in v:
            if not re.match(r"^https?://", url):
                raise ValueError(f"'{url}' must start with http:// or https://")
        return v


class CreateResearchRequest(ResearchValidatorMixin):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=10)
    category: Optional[str] = None
    tags: list[str] = Field(default=[], max_length=20)
    references: list[str] = []
    images: list[str] = []


class UpdateResearchRequest(ResearchValidatorMixin):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, min_length=10)
    status: Optional[ResearchStatus] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = Field(default=None, max_length=20)
    references: Optional[list[str]] = None
    images: Optional[list[str]] = None