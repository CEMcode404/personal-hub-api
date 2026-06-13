from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from src.constants.todo import TodoStatus, RecurrencePattern


class CreateTodoRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, max_length=2000)
    is_recurring: bool = False
    recurrence: Optional[RecurrencePattern] = None
    next_occurrence_at: Optional[str] = None
    notify: bool = False
    notify_at: Optional[str] = None
    notify_sms: bool = False
    notify_web: bool = False

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty or whitespace")
        return v

    @field_validator("body")
    @classmethod
    def strip_body(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None

    @field_validator("notify_at", "next_occurrence_at")
    @classmethod
    def validate_datetime(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("must be a valid ISO 8601 datetime")
        return v

    @model_validator(mode="after")
    def validate_fields(self):
        if self.notify and not self.notify_at:
            raise ValueError("notify_at is required when notify is enabled")
        if self.is_recurring and not (self.recurrence and self.next_occurrence_at):
            raise ValueError("recurrence and next_occurrence_at are required when is_recurring is enabled")
        if self.notify_at and self.next_occurrence_at and self.notify_at > self.next_occurrence_at:
            raise ValueError("notify_at must be earlier than or equal to next_occurrence_at")
        return self


class UpdateTodoRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TodoStatus] = None
    is_recurring: Optional[bool] = None
    recurrence: Optional[RecurrencePattern] = None
    next_occurrence_at: Optional[str] = None
    notify: Optional[bool] = None
    notify_at: Optional[str] = None
    notify_sms: Optional[bool] = None
    notify_web: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty or whitespace")
        return v

    @field_validator("body")
    @classmethod
    def strip_body(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None

    @field_validator("notify_at", "next_occurrence_at")
    @classmethod
    def validate_datetime(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("must be a valid ISO 8601 datetime")
        return v

    @model_validator(mode="after")
    def validate_fields(self):
        if self.notify and not self.notify_at:
            raise ValueError("notify_at is required when notify is enabled")
        if self.is_recurring and not (self.recurrence and self.next_occurrence_at):
            raise ValueError("recurrence and next_occurrence_at are required when is_recurring is enabled")
        if self.notify_at and self.next_occurrence_at and self.notify_at > self.next_occurrence_at:
            raise ValueError("notify_at must be earlier than or equal to next_occurrence_at")
        return self