from enum import Enum

class NotificationStatus(str, Enum):
    unread = "unread"
    read = "read"