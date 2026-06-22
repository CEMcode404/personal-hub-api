from dataclasses import dataclass
from typing import Optional
from constants.notification import NotificationStatus


@dataclass
class Notification:
    id: str
    title: str
    message: str
    status: NotificationStatus
    todo_id: str
    created_at: str
    ttl: Optional[int] = None