from enum import Enum

class ContentType(str, Enum):
    article = "article"
    til = "til"
    tutorial = "tutorial"
    snippet = "snippet"
    project = "project"


class ContentStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"