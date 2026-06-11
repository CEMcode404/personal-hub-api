import re
import nh3
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from src.constants.content import ALLOWED_TAGS, ALLOWED_ATTRIBUTES

BODY_CLEANER = nh3.Cleaner(
    tags=ALLOWED_TAGS,
    attributes=ALLOWED_ATTRIBUTES,
    url_schemes={"http", "https", "mailto"},
    link_rel="noopener noreferrer",
    filter_style_properties={"width", "text-align", "color", "background-color"},
)

class WikiValidatorMixin(BaseModel):
    @field_validator("title", mode="before", check_fields=False)
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

    @field_validator("cover_image", mode="before", check_fields=False)
    @classmethod
    def validate_cover_image(cls, v):
        if v and not re.match(r"^https?://", v):
            raise ValueError("Must start with http:// or https://")
        return v

    @field_validator("links", mode="before", check_fields=False)
    @classmethod
    def validate_links(cls, v):
        if v is None:
            return v
        for url in v:
            if not re.match(r"^https?://", url):
                raise ValueError(f"'{url}' must start with http:// or https://")
        return v

    @field_validator("related", mode="before", check_fields=False)
    @classmethod
    def validate_related(cls, v):
        if v is None:
            return v
        for id in v:
            try:
                str(id)
            except Exception:
                raise ValueError(f"'{id}' is not a valid ID")
        return v


class CreateWikiRequest(WikiValidatorMixin):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    category: Optional[str] = None
    tags: list[str] = Field(default=[], max_length=20)
    cover_image: Optional[str] = None
    is_pinned: bool = False
    links: list[str] = []
    related: list[str] = []


class UpdateWikiRequest(WikiValidatorMixin):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, min_length=1)
    category: Optional[str] = None
    tags: Optional[list[str]] = Field(default=None, max_length=20)
    cover_image: Optional[str] = None
    is_pinned: Optional[bool] = None
    links: Optional[list[str]] = None
    related: Optional[list[str]] = None