from enum import Enum

class TodoStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"

class RecurrencePattern(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    semi_annual = "semi-annual"
    annual = "annual"

class ScheduleAction(str, Enum):
    notify = "notify"
    recur = "recur"