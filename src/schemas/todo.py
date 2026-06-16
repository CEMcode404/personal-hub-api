import nh3
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime, timezone, timedelta
from src.constants.todo import TodoStatus, RecurrencePattern

MAX_RECURRENCE_HORIZON = timedelta(days=730)  # 2 years


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
        v = nh3.clean(v, tags=set()).strip()
        if not v:
            raise ValueError("title cannot be empty or whitespace")
        return v

    @field_validator("body")
    @classmethod
    def strip_body(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = nh3.clean(v, tags=set()).strip()
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
        now = datetime.now(timezone.utc)

        if self.notify and not self.notify_at:
            raise ValueError("notify_at is required when notify is enabled")

        if self.is_recurring and not (self.recurrence and self.next_occurrence_at):
            raise ValueError("recurrence and next_occurrence_at are required when is_recurring is enabled")

        notify_dt = None
        if self.notify_at:
            notify_dt = datetime.fromisoformat(self.notify_at)
            if notify_dt.tzinfo is None:
                notify_dt = notify_dt.replace(tzinfo=timezone.utc)
            if notify_dt < now:
                raise ValueError("notify_at cannot be in the past")

        next_dt = None
        if self.next_occurrence_at:
            next_dt = datetime.fromisoformat(self.next_occurrence_at)
            if next_dt.tzinfo is None:
                next_dt = next_dt.replace(tzinfo=timezone.utc)
            if next_dt < now:
                raise ValueError("next_occurrence_at cannot be in the past")
            if next_dt > now + MAX_RECURRENCE_HORIZON:
                raise ValueError("next_occurrence_at cannot be more than 2 years in the future")

        if notify_dt and next_dt and notify_dt > next_dt:
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
        v = nh3.clean(v, tags=set()).strip()
        if not v:
            raise ValueError("title cannot be empty or whitespace")
        return v

    @field_validator("body")
    @classmethod
    def strip_body(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = nh3.clean(v, tags=set()).strip()
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
        now = datetime.now(timezone.utc)

        if self.notify and not self.notify_at:
            raise ValueError("notify_at is required when notify is enabled")

        if self.is_recurring and not (self.recurrence and self.next_occurrence_at):
            raise ValueError("recurrence and next_occurrence_at are required when is_recurring is enabled")

        notify_dt = None
        if self.notify_at:
            notify_dt = datetime.fromisoformat(self.notify_at)
            if notify_dt.tzinfo is None:
                notify_dt = notify_dt.replace(tzinfo=timezone.utc)
            if notify_dt < now:
                raise ValueError("notify_at cannot be in the past")

        next_dt = None
        if self.next_occurrence_at:
            next_dt = datetime.fromisoformat(self.next_occurrence_at)
            if next_dt.tzinfo is None:
                next_dt = next_dt.replace(tzinfo=timezone.utc)
            if next_dt < now:
                raise ValueError("next_occurrence_at cannot be in the past")
            if next_dt > now + MAX_RECURRENCE_HORIZON:
                raise ValueError("next_occurrence_at cannot be more than 2 years in the future")

        if notify_dt and next_dt and notify_dt > next_dt:
            raise ValueError("notify_at must be earlier than or equal to next_occurrence_at")

        return self