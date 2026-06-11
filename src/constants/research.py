from enum import Enum

class ResearchStatus(str, Enum):
    draft = "draft"
    in_progress = "in_progress"
    completed = "completed"
    archived = "archived"
