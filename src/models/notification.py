from dataclasses import dataclass
from typing import Optional

@dataclass
class Notification:
    id: str
    title: str
    message: str
    status: str        # unread, read
    todo_id: str
    created_at: str
    ttl: Optional[int] = None  # Unix timestamp for DynamoDB TTL