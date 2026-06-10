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

ALLOWED_TAGS = {
    "p", "br", "strong", "em", "u", "s", "code", "pre", "blockquote",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "hr",
    "a", "img",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "colgroup", "col",
    "span", "div", "mark",
}

ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "title", "width", "height"},
    "td": {"colspan", "rowspan", "style"},
    "th": {"colspan", "rowspan", "style"},
    "span": {"style", "class"},
    "mark": {"style"},
}