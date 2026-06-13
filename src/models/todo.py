from dataclasses import dataclass
from typing import Optional
from src.constants.todo import TodoStatus, RecurrencePattern


@dataclass
class Todo:
    id: str
    title: str
    status: TodoStatus
    is_recurring: bool
    notify: bool
    notify_sms: bool
    notify_web: bool
    created_at: str
    updated_at: str
    body: Optional[str] = None
    recurrence: Optional[RecurrencePattern] = None
    notify_at: Optional[str] = None
    next_occurrence_at: Optional[str] = None
    recurring_parent_id: Optional[str] = None
    ttl: Optional[int] = None