from dataclasses import dataclass
from typing import Optional

@dataclass
class Todo:
    id: str
    title: str
    status: str
    is_recurring: bool
    notify: bool
    notify_sms: bool
    notify_web: bool
    created_at: str
    updated_at: str
    body: Optional[str] = None
    recurrence: Optional[str] = None
    notify_at: Optional[str] = None