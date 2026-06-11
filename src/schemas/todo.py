import re
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from src.constants.todo import TodoStatus, RecurrencePattern


class CreateTodoRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, max_length=2000)
    is_recurring: bool = False
    recurrence: Optional[RecurrencePattern] = None
    notify: bool = False
    notify_at: Optional[str] = None
    notify_sms: bool = False
    notify_web: bool = False

    @model_validator(mode="after")
    def validate_fields(self):
        if self.notify and not self.notify_at:
            raise ValueError("notify_at is required when notify is enabled")
        if self.is_recurring and not self.recurrence:
            raise ValueError("recurrence is required when is_recurring is enabled")
        return self


class UpdateTodoRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TodoStatus] = None
    is_recurring: Optional[bool] = None
    recurrence: Optional[RecurrencePattern] = None
    notify: Optional[bool] = None
    notify_at: Optional[str] = None
    notify_sms: Optional[bool] = None
    notify_web: Optional[bool] = None

    @model_validator(mode="after")
    def validate_fields(self):
        if self.notify and not self.notify_at:
            raise ValueError("notify_at is required when notify is enabled")
        if self.is_recurring and not self.recurrence:
            raise ValueError("recurrence is required when is_recurring is enabled")
        return self