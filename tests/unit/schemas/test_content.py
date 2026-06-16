import pytest
from pydantic import ValidationError
from src.schemas.content import CreateContentRequest, UpdateContentRequest
from src.constants.content import ContentType, ContentStatus


VALID_BODY = "This is a valid content body text."
VALID_TITLE = "Valid Content Title"


class TestCreateContentRequest:

    # --- Title ---
    def test_minimal_valid(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY)
        assert content.title == VALID_TITLE
        assert content.type == ContentType.article

    def test_title_required(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(body=VALID_BODY)

    def test_title_empty_raises(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title="", body=VALID_BODY)

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title="a" * 256, body=VALID_BODY)

    def test_title_exact_max_length_valid(self):
        content = CreateContentRequest(title="a" * 255, body=VALID_BODY)
        assert len(content.title) == 255

    def test_title_strips_html(self):
        content = CreateContentRequest(title="<script>alert(1)</script>Title", body=VALID_BODY)
        assert "<script>" not in content.title
        assert "Title" in content.title

    def test_title_whitespace_stripped(self):
        content = CreateContentRequest(title="  Hello  ", body=VALID_BODY)
        assert content.title == "Hello"

    def test_title_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title="<script>alert(1)</script>", body=VALID_BODY)

    # --- Body ---
    def test_body_required(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title=VALID_TITLE)

    def test_body_too_short_raises(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title=VALID_TITLE, body="short")

    def test_body_exact_min_length_valid(self):
        content = CreateContentRequest(title=VALID_TITLE, body="a" * 10)
        assert len(content.body) >= 10

    def test_body_removes_script_tags(self):
        content = CreateContentRequest(title=VALID_TITLE, body="<script>alert(1)</script><p>Safe content here</p>")
        assert "<script>" not in content.body
        assert "Safe content here" in content.body

    def test_body_keeps_allowed_tags(self):
        content = CreateContentRequest(title=VALID_TITLE, body="<p>Para</p><strong>Bold</strong>")
        assert "Para" in content.body
        assert "Bold" in content.body

    def test_body_blocks_javascript_links(self):
        content = CreateContentRequest(title=VALID_TITLE, body='<a href="javascript:void(0)">Click</a> filler text')
        assert "javascript:" not in content.body

    def test_body_none_raises(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title=VALID_TITLE, body=None)

    def test_body_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title=VALID_TITLE, body="<b>hi</b>")

    # --- Type ---
    def test_type_defaults_to_article(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY)
        assert content.type == ContentType.article

    def test_type_explicit_valid(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, type=ContentType.tutorial)
        assert content.type == ContentType.tutorial

    def test_type_all_enum_values_valid(self):
        for content_type in ContentType:
            content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, type=content_type)
            assert content.type == content_type

    def test_type_invalid_value_raises(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, type="not_a_real_type")

    # --- Excerpt ---
    def test_excerpt_optional(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY)
        assert content.excerpt is None

    def test_excerpt_valid(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, excerpt="A short summary")
        assert content.excerpt == "A short summary"

    def test_excerpt_strips_html(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, excerpt="<script>xss</script>Summary")
        assert "<script>" not in content.excerpt
        assert "Summary" in content.excerpt

    def test_excerpt_whitespace_stripped_to_empty_not_none(self):
        # NOTE: excerpt shares sanitize_plain with title, which does not
        # collapse whitespace-only input to None (unlike category in other schemas)
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, excerpt="   ")
        assert content.excerpt == ""

    def test_excerpt_max_length(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, excerpt="a" * 501)

    def test_excerpt_exact_max_length_valid(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, excerpt="a" * 500)
        assert len(content.excerpt) == 500

    # --- Tags ---
    def test_tags_default_empty(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY)
        assert content.tags == []

    def test_tags_lowercased(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, tags=["Python", "AI"])
        assert content.tags == ["python", "ai"]

    def test_tags_strips_html(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, tags=["<b>python</b>"])
        assert content.tags == ["python"]

    def test_tag_too_long_raises(self):
        with pytest.raises(ValidationError, match="exceeds 50 characters"):
            CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, tags=["a" * 51])

    def test_tag_invalid_characters_raises(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, tags=["bad tag!"])

    def test_tag_hyphen_underscore_allowed(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, tags=["machine-learning", "tag_name"])
        assert content.tags == ["machine-learning", "tag_name"]

    def test_too_many_tags_raises(self):
        with pytest.raises(ValidationError):
            CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, tags=[f"tag{i}" for i in range(21)])

    def test_tag_pure_html_invalid_after_sanitize(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, tags=["<script></script>"])

    # --- Cover image ---
    def test_cover_image_optional(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY)
        assert content.cover_image is None

    def test_cover_image_valid(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, cover_image="https://example.com/img.png")
        assert content.cover_image == "https://example.com/img.png"

    def test_cover_image_invalid_scheme_raises(self):
        with pytest.raises(ValidationError, match="Must start with http"):
            CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, cover_image="ftp://example.com/img.png")

    def test_cover_image_empty_string_valid(self):
        content = CreateContentRequest(title=VALID_TITLE, body=VALID_BODY, cover_image="")
        assert content.cover_image == ""


class TestUpdateContentRequest:

    def test_all_fields_optional(self):
        content = UpdateContentRequest()
        assert content.title is None
        assert content.body is None
        assert content.type is None
        assert content.status is None
        assert content.excerpt is None
        assert content.tags is None
        assert content.cover_image is None

    def test_title_strips_html(self):
        content = UpdateContentRequest(title="<script>xss</script>Hello")
        assert "<script>" not in content.title
        assert "Hello" in content.title

    def test_title_empty_string_raises(self):
        with pytest.raises(ValidationError):
            UpdateContentRequest(title="")

    def test_title_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            UpdateContentRequest(title="<script>alert(1)</script>")

    def test_body_too_short_raises(self):
        with pytest.raises(ValidationError):
            UpdateContentRequest(body="short")

    def test_body_removes_script(self):
        content = UpdateContentRequest(body="<script>xss</script><p>Valid content here</p>")
        assert "<script>" not in content.body

    def test_body_none_valid(self):
        content = UpdateContentRequest(body=None)
        assert content.body is None

    def test_body_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            UpdateContentRequest(body="<b>hi</b>")

    def test_type_update(self):
        content = UpdateContentRequest(type=ContentType.snippet)
        assert content.type == ContentType.snippet

    def test_type_invalid_raises(self):
        with pytest.raises(ValidationError):
            UpdateContentRequest(type="not_a_real_type")

    def test_status_update(self):
        content = UpdateContentRequest(status=ContentStatus.published)
        assert content.status == ContentStatus.published

    def test_status_all_enum_values_valid(self):
        for status in ContentStatus:
            content = UpdateContentRequest(status=status)
            assert content.status == status

    def test_status_invalid_raises(self):
        with pytest.raises(ValidationError):
            UpdateContentRequest(status="not_a_real_status")

    def test_excerpt_strips_html(self):
        content = UpdateContentRequest(excerpt="<script>xss</script>Summary")
        assert "<script>" not in content.excerpt
        assert "Summary" in content.excerpt

    def test_excerpt_max_length(self):
        with pytest.raises(ValidationError):
            UpdateContentRequest(excerpt="a" * 501)

    def test_tags_none_valid(self):
        content = UpdateContentRequest(tags=None)
        assert content.tags is None

    def test_tags_lowercased(self):
        content = UpdateContentRequest(tags=["PYTHON"])
        assert content.tags == ["python"]

    def test_tag_invalid_characters_raises(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            UpdateContentRequest(tags=["bad tag!"])

    def test_too_many_tags_raises(self):
        with pytest.raises(ValidationError):
            UpdateContentRequest(tags=[f"tag{i}" for i in range(21)])

    def test_cover_image_invalid_scheme_raises(self):
        with pytest.raises(ValidationError, match="Must start with http"):
            UpdateContentRequest(cover_image="ftp://example.com")

    def test_cover_image_none_valid(self):
        content = UpdateContentRequest(cover_image=None)
        assert content.cover_image is None

    def test_partial_update_only_title(self):
        content = UpdateContentRequest(title="New Title")
        assert content.title == "New Title"
        assert content.body is None

    def test_partial_update_only_status(self):
        content = UpdateContentRequest(status=ContentStatus.archived)
        assert content.status == ContentStatus.archived
        assert content.title is None

    def test_full_update_valid(self):
        content = UpdateContentRequest(
            title="Updated Title",
            body="Updated body content that is long enough",
            type=ContentType.project,
            status=ContentStatus.published,
            excerpt="Updated excerpt",
            tags=["python", "ai"],
            cover_image="https://example.com/img.png",
        )
        assert content.title == "Updated Title"
        assert content.type == ContentType.project
        assert content.status == ContentStatus.published