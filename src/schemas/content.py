import re
import nh3
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from src.constants.content import ContentType, ContentStatus, ALLOWED_TAGS, ALLOWED_ATTRIBUTES


class ContentValidatorMixin(BaseModel):
    @field_validator("title", "excerpt", mode="before", check_fields=False)
    @classmethod
    def sanitize_plain(cls, v):
        if v is None:
            return v
        return nh3.clean(v, tags=set()).strip()
    
    @field_validator("body", mode="before", check_fields=False)
    @classmethod
    def sanitize_body(cls, v):
        if v is None:
            return v
        return nh3.clean(v, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
    
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

    @field_validator("cover_image", mode="before", check_fields=False)
    @classmethod
    def validate_url(cls, v):
        if v and not re.match(r"^https?://", v):
            raise ValueError("Must start with http:// or https://")
        return v


class CreateContentRequest(ContentValidatorMixin):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=10)
    type: ContentType = ContentType.article
    excerpt: Optional[str] = Field(default=None, max_length=500)
    tags: list[str] = Field(default=[], max_length=20)
    cover_image: Optional[str] = None


class UpdateContentRequest(ContentValidatorMixin):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, min_length=10)
    type: Optional[ContentType] = None
    status: Optional[ContentStatus] = None
    excerpt: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[list[str]] = Field(default=None, max_length=20)
    cover_image: Optional[str] = None