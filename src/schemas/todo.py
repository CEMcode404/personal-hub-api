from pydantic import BaseModel, model_validator
from typing import Optional

class CreateTodoRequest(BaseModel):
    title: str
    body: Optional[str] = None
    is_recurring: bool = False
    recurrence: Optional[str] = None
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
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence: Optional[str] = None
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