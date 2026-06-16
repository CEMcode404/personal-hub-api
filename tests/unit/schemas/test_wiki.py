import pytest
import uuid
from pydantic import ValidationError
from src.schemas.wiki import CreateWikiRequest, UpdateWikiRequest


VALID_BODY = "This is a valid wiki body."
VALID_TITLE = "Valid Wiki Title"


class TestCreateWikiRequest:

    # --- Title ---
    def test_minimal_valid(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY)
        assert wiki.title == VALID_TITLE

    def test_title_required(self):
        with pytest.raises(ValidationError):
            CreateWikiRequest(body=VALID_BODY)

    def test_title_empty_raises(self):
        with pytest.raises(ValidationError):
            CreateWikiRequest(title="", body=VALID_BODY)

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            CreateWikiRequest(title="a" * 256, body=VALID_BODY)

    def test_title_exact_max_length_valid(self):
        wiki = CreateWikiRequest(title="a" * 255, body=VALID_BODY)
        assert len(wiki.title) == 255

    def test_title_strips_html(self):
        wiki = CreateWikiRequest(title="<script>alert(1)</script>Title", body=VALID_BODY)
        assert "<script>" not in wiki.title
        assert "Title" in wiki.title

    def test_title_whitespace_stripped(self):
        wiki = CreateWikiRequest(title="  Hello  ", body=VALID_BODY)
        assert wiki.title == "Hello"

    def test_title_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            CreateWikiRequest(title="<script>alert(1)</script>", body=VALID_BODY)

    # --- Body ---
    def test_body_required(self):
        with pytest.raises(ValidationError):
            CreateWikiRequest(title=VALID_TITLE)

    def test_body_removes_script_tags(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body="<script>alert(1)</script><p>Safe</p>")
        assert "<script>" not in wiki.body
        assert "Safe" in wiki.body

    def test_body_keeps_allowed_tags(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body="<p>Para</p><strong>Bold</strong>")
        assert "Para" in wiki.body
        assert "Bold" in wiki.body

    def test_body_blocks_javascript_links(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body='<a href="javascript:void(0)">Click</a>')
        assert "javascript:" not in wiki.body

    def test_body_none_raises(self):
        with pytest.raises(ValidationError):
            CreateWikiRequest(title=VALID_TITLE, body=None)

    def test_body_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            CreateWikiRequest(title=VALID_TITLE, body="<script></script>")

    # --- Category ---
    def test_category_optional(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY)
        assert wiki.category is None

    def test_category_explicit_none_valid(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, category=None)
        assert wiki.category is None

    def test_category_strips_html(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, category="<script>xss</script>Tech")
        assert "<script>" not in wiki.category
        assert "Tech" in wiki.category

    def test_category_whitespace_only_becomes_none(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, category="   ")
        assert wiki.category is None

    # --- Tags ---
    def test_tags_default_empty(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY)
        assert wiki.tags == []

    def test_tags_lowercased(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, tags=["Python", "AI"])
        assert wiki.tags == ["python", "ai"]

    def test_tags_strips_html(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, tags=["<b>python</b>"])
        assert wiki.tags == ["python"]

    def test_tag_too_long_raises(self):
        with pytest.raises(ValidationError, match="exceeds 50 characters"):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, tags=["a" * 51])

    def test_tag_invalid_characters_raises(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, tags=["bad tag!"])

    def test_tag_hyphen_underscore_allowed(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, tags=["machine-learning", "tag_name"])
        assert wiki.tags == ["machine-learning", "tag_name"]

    def test_too_many_tags_raises(self):
        with pytest.raises(ValidationError):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, tags=[f"tag{i}" for i in range(21)])

    def test_tag_pure_html_invalid_after_sanitize(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, tags=["<script></script>"])

    # --- Cover image ---
    def test_cover_image_optional(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY)
        assert wiki.cover_image is None

    def test_cover_image_valid(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, cover_image="https://example.com/img.png")
        assert wiki.cover_image == "https://example.com/img.png"

    def test_cover_image_invalid_scheme_raises(self):
        with pytest.raises(ValidationError, match="Must start with http"):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, cover_image="ftp://example.com/img.png")

    def test_cover_image_empty_string_valid(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, cover_image="")
        assert wiki.cover_image == ""

    # --- is_pinned ---
    def test_is_pinned_default_false(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY)
        assert wiki.is_pinned is False

    def test_is_pinned_true(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, is_pinned=True)
        assert wiki.is_pinned is True

    # --- Links ---
    def test_links_default_empty(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY)
        assert wiki.links == []

    def test_links_valid(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, links=["https://example.com"])
        assert wiki.links == ["https://example.com"]

    def test_links_invalid_scheme_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, links=["ftp://example.com"])

    def test_links_javascript_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, links=["javascript:void(0)"])

    # --- Related ---
    def test_related_default_empty(self):
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY)
        assert wiki.related == []

    def test_related_valid_uuid(self):
        valid_id = str(uuid.uuid4())
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, related=[valid_id])
        assert wiki.related == [valid_id]

    def test_related_multiple_valid_uuids(self):
        ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        wiki = CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, related=ids)
        assert len(wiki.related) == 2

    def test_related_invalid_uuid_raises(self):
        with pytest.raises(ValidationError, match="is not a valid UUID"):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, related=["not-a-uuid"])

    def test_related_empty_string_raises(self):
        with pytest.raises(ValidationError, match="is not a valid UUID"):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, related=[""])

    def test_related_random_text_raises(self):
        with pytest.raises(ValidationError, match="is not a valid UUID"):
            CreateWikiRequest(title=VALID_TITLE, body=VALID_BODY, related=["12345"])


class TestUpdateWikiRequest:

    def test_all_fields_optional(self):
        wiki = UpdateWikiRequest()
        assert wiki.title is None
        assert wiki.body is None
        assert wiki.category is None
        assert wiki.tags is None
        assert wiki.cover_image is None
        assert wiki.is_pinned is None
        assert wiki.links is None
        assert wiki.related is None

    def test_title_strips_html(self):
        wiki = UpdateWikiRequest(title="<script>xss</script>Hello")
        assert "<script>" not in wiki.title
        assert "Hello" in wiki.title

    def test_title_empty_string_raises(self):
        with pytest.raises(ValidationError):
            UpdateWikiRequest(title="")

    def test_title_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            UpdateWikiRequest(title="<script>alert(1)</script>")

    def test_body_none_valid(self):
        wiki = UpdateWikiRequest(body=None)
        assert wiki.body is None

    def test_body_removes_script(self):
        wiki = UpdateWikiRequest(body="<script>xss</script><p>Valid</p>")
        assert "<script>" not in wiki.body

    def test_body_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            UpdateWikiRequest(body="<script></script>")

    def test_category_strips_html(self):
        wiki = UpdateWikiRequest(category="<script>xss</script>Tech")
        assert "<script>" not in wiki.category
        assert "Tech" in wiki.category

    def test_category_whitespace_only_becomes_none(self):
        wiki = UpdateWikiRequest(category="   ")
        assert wiki.category is None

    def test_tags_none_valid(self):
        wiki = UpdateWikiRequest(tags=None)
        assert wiki.tags is None

    def test_tags_lowercased(self):
        wiki = UpdateWikiRequest(tags=["PYTHON"])
        assert wiki.tags == ["python"]

    def test_tag_invalid_characters_raises(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            UpdateWikiRequest(tags=["bad tag!"])

    def test_too_many_tags_raises(self):
        with pytest.raises(ValidationError):
            UpdateWikiRequest(tags=[f"tag{i}" for i in range(21)])

    def test_cover_image_invalid_scheme_raises(self):
        with pytest.raises(ValidationError, match="Must start with http"):
            UpdateWikiRequest(cover_image="ftp://example.com")

    def test_cover_image_none_valid(self):
        wiki = UpdateWikiRequest(cover_image=None)
        assert wiki.cover_image is None

    def test_is_pinned_update(self):
        wiki = UpdateWikiRequest(is_pinned=True)
        assert wiki.is_pinned is True

    def test_links_none_valid(self):
        wiki = UpdateWikiRequest(links=None)
        assert wiki.links is None

    def test_links_invalid_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            UpdateWikiRequest(links=["not-a-url"])

    def test_related_none_valid(self):
        wiki = UpdateWikiRequest(related=None)
        assert wiki.related is None

    def test_related_valid_uuid(self):
        valid_id = str(uuid.uuid4())
        wiki = UpdateWikiRequest(related=[valid_id])
        assert wiki.related == [valid_id]

    def test_related_invalid_uuid_raises(self):
        with pytest.raises(ValidationError, match="is not a valid UUID"):
            UpdateWikiRequest(related=["not-a-uuid"])

    def test_partial_update_only_title(self):
        wiki = UpdateWikiRequest(title="New Title")
        assert wiki.title == "New Title"
        assert wiki.body is None

    def test_partial_update_only_tags(self):
        wiki = UpdateWikiRequest(tags=["python"])
        assert wiki.tags == ["python"]
        assert wiki.title is None

    def test_full_update_valid(self):
        valid_id = str(uuid.uuid4())
        wiki = UpdateWikiRequest(
            title="Updated Title",
            body="Updated body",
            category="Science",
            tags=["python", "ai"],
            cover_image="https://example.com/img.png",
            is_pinned=True,
            links=["https://example.com"],
            related=[valid_id],
        )
        assert wiki.title == "Updated Title"
        assert wiki.is_pinned is True
        assert wiki.related == [valid_id]