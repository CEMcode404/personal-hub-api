from dataclasses import dataclass
from typing import Optional
from constants.todo import TodoStatus, RecurrencePattern, TodoParent


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
    recurring_parent_id: str = TodoParent.standalone.value
    gsi_order_sk: Optional[str] = None
    status_sk: Optional[str] = None
    ttl: Optional[int] = None