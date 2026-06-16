import pytest
from pydantic import ValidationError
from src.schemas.research import CreateResearchRequest, UpdateResearchRequest
from src.constants.research import ResearchStatus


VALID_BODY = "This is a valid body text that meets minimum length"
VALID_TITLE = "Valid Research Title"


class TestCreateResearchRequest:

    # --- Title ---
    def test_minimal_valid(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY)
        assert research.title == VALID_TITLE

    def test_title_required(self):
        with pytest.raises(ValidationError):
            CreateResearchRequest(body=VALID_BODY)

    def test_title_empty_raises(self):
        with pytest.raises(ValidationError):
            CreateResearchRequest(title="", body=VALID_BODY)

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            CreateResearchRequest(title="a" * 256, body=VALID_BODY)

    def test_title_exact_max_length_valid(self):
        research = CreateResearchRequest(title="a" * 255, body=VALID_BODY)
        assert len(research.title) == 255

    def test_title_strips_html_tags(self):
        research = CreateResearchRequest(title="<b>Hello</b>", body=VALID_BODY)
        assert research.title == "Hello"

    def test_title_strips_script_tag(self):
        research = CreateResearchRequest(title="<script>alert('xss')</script>Title", body=VALID_BODY)
        assert "<script>" not in research.title
        assert "Title" in research.title

    def test_title_strips_nested_html(self):
        research = CreateResearchRequest(title="<div><span>Hello</span></div>", body=VALID_BODY)
        assert research.title == "Hello"

    def test_title_strips_html_attributes(self):
        research = CreateResearchRequest(title='<p style="color:red">Hello</p>', body=VALID_BODY)
        assert "style" not in research.title
        assert "Hello" in research.title

    def test_title_whitespace_stripped(self):
        research = CreateResearchRequest(title="  Hello  ", body=VALID_BODY)
        assert research.title == "Hello"
    
    def test_title_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            UpdateResearchRequest(title="<script>alert(1)</script>")

    def test_title_with_special_characters_preserved(self):
        research = CreateResearchRequest(title="Research: AI & ML (2026)", body=VALID_BODY)
        assert "AI &amp; ML" in research.title

    def test_title_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            CreateResearchRequest(title="<script>alert(1)</script>", body=VALID_BODY)

    # --- Body ---
    def test_body_required(self):
        with pytest.raises(ValidationError):
            CreateResearchRequest(title=VALID_TITLE)

    def test_body_too_short_raises(self):
        with pytest.raises(ValidationError):
            CreateResearchRequest(title=VALID_TITLE, body="short")

    def test_body_exact_min_length_valid(self):
        research = CreateResearchRequest(title=VALID_TITLE, body="a" * 10)
        assert len(research.body) >= 10

    def test_body_removes_script_tags(self):
        research = CreateResearchRequest(
            title=VALID_TITLE,
            body="<script>alert('xss')</script><p>Safe content here</p>"
        )
        assert "<script>" not in research.body
        assert "Safe content here" in research.body

    def test_body_keeps_allowed_tags(self):
        research = CreateResearchRequest(
            title=VALID_TITLE,
            body="<p>Paragraph</p><strong>Bold</strong><em>Italic</em>"
        )
        assert "Paragraph" in research.body
        assert "Bold" in research.body
        assert "Italic" in research.body

    def test_body_removes_on_event_attributes(self):
        research = CreateResearchRequest(
            title=VALID_TITLE,
            body='<p onclick="evil()">Hello</p>'
        )
        assert "onclick" not in research.body

    def test_body_allows_http_links(self):
        research = CreateResearchRequest(
            title=VALID_TITLE,
            body='<a href="https://example.com">Click here</a>'
        )
        assert "example.com" in research.body

    def test_body_blocks_javascript_links(self):
        research = CreateResearchRequest(
            title=VALID_TITLE,
            body='<a href="javascript:void(0)">Click</a>'
        )
        assert "javascript:" not in research.body

    def test_body_none_raises(self):
        with pytest.raises(ValidationError):
            CreateResearchRequest(title=VALID_TITLE, body=None)

    def test_body_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            CreateResearchRequest(title=VALID_TITLE, body="<b>hi</b>")

    # --- Category ---
    def test_category_optional(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY)
        assert research.category is None

    def test_category_explicit_none_valid(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, category=None)
        assert research.category is None

    def test_category_valid(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, category="AI")
        assert research.category == "AI"

    def test_category_strips_html(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, category="<script>xss</script>AI")
        assert "<script>" not in research.category
        assert "AI" in research.category

    def test_category_whitespace_only_becomes_none(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, category="   ")
        assert research.category is None

    # --- Tags ---
    def test_tags_default_empty(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY)
        assert research.tags == []

    def test_tags_valid(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["python", "ai"])
        assert research.tags == ["python", "ai"]

    def test_tags_lowercased(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["Python", "ML"])
        assert research.tags == ["python", "ml"]

    def test_tags_stripped_whitespace(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["  python  "])
        assert research.tags == ["python"]

    def test_tags_strips_html(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["<b>python</b>"])
        assert research.tags == ["python"]

    def test_tag_too_long_raises(self):
        with pytest.raises(ValidationError, match="exceeds 50 characters"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["a" * 51])

    def test_tag_exact_max_length_valid(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["a" * 50])
        assert len(research.tags[0]) == 50

    def test_tag_invalid_characters_raises(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["invalid tag!"])

    def test_tag_with_space_raises(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["hello world"])

    def test_tag_with_special_chars_raises(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["tag@name"])

    def test_tag_hyphen_allowed(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["machine-learning"])
        assert research.tags == ["machine-learning"]

    def test_tag_underscore_allowed(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["tag_name"])
        assert research.tags == ["tag_name"]

    def test_too_many_tags_raises(self):
        with pytest.raises(ValidationError):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=[f"tag{i}" for i in range(21)])

    def test_exact_max_tags_valid(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=[f"tag{i}" for i in range(20)])
        assert len(research.tags) == 20

    def test_empty_tags_list_valid(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=[])
        assert research.tags == []

    def test_tag_pure_html_invalid_after_sanitize(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["<script></script>"])

    def test_one_invalid_tag_among_valid_fails_entire_request(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, tags=["python", "<script></script>"])

    # --- References ---
    def test_references_default_empty(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY)
        assert research.references == []

    def test_references_valid_https(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, references=["https://example.com"])
        assert research.references == ["https://example.com"]

    def test_references_valid_http(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, references=["http://example.com"])
        assert research.references == ["http://example.com"]

    def test_references_multiple_valid(self):
        urls = ["https://one.com", "https://two.com", "http://three.com"]
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, references=urls)
        assert len(research.references) == 3

    def test_references_invalid_ftp_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, references=["ftp://invalid.com"])

    def test_references_no_scheme_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, references=["example.com"])

    def test_references_javascript_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, references=["javascript:void(0)"])

    def test_references_empty_string_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, references=[""])

    # --- Images ---
    def test_images_default_empty(self):
        research = CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY)
        assert research.images == []

    def test_images_valid(self):
        research = CreateResearchRequest(
            title=VALID_TITLE, body=VALID_BODY,
            images=["https://example.com/image.png"]
        )
        assert len(research.images) == 1

    def test_images_multiple_valid(self):
        research = CreateResearchRequest(
            title=VALID_TITLE, body=VALID_BODY,
            images=["https://a.com/1.png", "https://b.com/2.jpg"]
        )
        assert len(research.images) == 2

    def test_images_invalid_url_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, images=["not-a-url"])

    def test_images_ftp_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            CreateResearchRequest(title=VALID_TITLE, body=VALID_BODY, images=["ftp://example.com/img.png"])


class TestUpdateResearchRequest:

    # --- All optional ---
    def test_all_fields_optional(self):
        research = UpdateResearchRequest()
        assert research.title is None
        assert research.body is None
        assert research.status is None
        assert research.tags is None
        assert research.references is None
        assert research.images is None
        assert research.category is None

    # --- Status ---
    def test_status_draft(self):
        research = UpdateResearchRequest(status=ResearchStatus.draft)
        assert research.status == ResearchStatus.draft

    def test_status_in_progress(self):
        research = UpdateResearchRequest(status=ResearchStatus.in_progress)
        assert research.status == ResearchStatus.in_progress

    def test_status_completed(self):
        research = UpdateResearchRequest(status=ResearchStatus.completed)
        assert research.status == ResearchStatus.completed

    def test_status_archived(self):
        research = UpdateResearchRequest(status=ResearchStatus.archived)
        assert research.status == ResearchStatus.archived

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            UpdateResearchRequest(status="invalid_status")

    def test_status_none_valid(self):
        research = UpdateResearchRequest(status=None)
        assert research.status is None

    # --- Title ---
    def test_title_strips_html(self):
        research = UpdateResearchRequest(title="<b>Hello</b>")
        assert research.title == "Hello"

    def test_title_script_removed(self):
        research = UpdateResearchRequest(title="<script>xss</script>Hello")
        assert "<script>" not in research.title
        assert "Hello" in research.title

    def test_title_too_long_raises(self):
        with pytest.raises(ValidationError):
            UpdateResearchRequest(title="a" * 256)

    def test_title_exact_max_length_valid(self):
        research = UpdateResearchRequest(title="a" * 255)
        assert len(research.title) == 255

    def test_title_empty_string_raises(self):
        with pytest.raises(ValidationError):
            UpdateResearchRequest(title="")

    def test_title_whitespace_stripped(self):
        research = UpdateResearchRequest(title="  Hello  ")
        assert research.title == "Hello"

    # --- Body ---
    def test_body_too_short_raises(self):
        with pytest.raises(ValidationError):
            UpdateResearchRequest(body="short")

    def test_body_removes_script(self):
        research = UpdateResearchRequest(body="<script>xss</script><p>Valid content here</p>")
        assert "<script>" not in research.body

    def test_body_none_valid(self):
        research = UpdateResearchRequest(body=None)
        assert research.body is None

    def test_body_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            UpdateResearchRequest(body="<b>hi</b>")

    # --- Category ---
    def test_category_strips_html(self):
        research = UpdateResearchRequest(category="<script>xss</script>AI")
        assert "<script>" not in research.category
        assert "AI" in research.category

    def test_category_whitespace_only_becomes_none(self):
        research = UpdateResearchRequest(category="   ")
        assert research.category is None

    def test_category_none_valid(self):
        research = UpdateResearchRequest(category=None)
        assert research.category is None

    # --- Tags ---
    def test_tags_none_valid(self):
        research = UpdateResearchRequest(tags=None)
        assert research.tags is None

    def test_tags_valid(self):
        research = UpdateResearchRequest(tags=["python", "ai"])
        assert research.tags == ["python", "ai"]

    def test_tags_lowercased(self):
        research = UpdateResearchRequest(tags=["PYTHON"])
        assert research.tags == ["python"]

    def test_tag_too_long_raises(self):
        with pytest.raises(ValidationError, match="exceeds 50 characters"):
            UpdateResearchRequest(tags=["a" * 51])

    def test_tag_invalid_characters_raises(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            UpdateResearchRequest(tags=["bad tag!"])

    def test_tag_hyphen_allowed(self):
        research = UpdateResearchRequest(tags=["deep-learning"])
        assert research.tags == ["deep-learning"]

    def test_too_many_tags_raises(self):
        with pytest.raises(ValidationError):
            UpdateResearchRequest(tags=[f"tag{i}" for i in range(21)])

    def test_tag_pure_html_invalid_after_sanitize(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            UpdateResearchRequest(tags=["<script></script>"])

    # --- References ---
    def test_references_none_valid(self):
        research = UpdateResearchRequest(references=None)
        assert research.references is None

    def test_references_valid(self):
        research = UpdateResearchRequest(references=["https://example.com"])
        assert research.references == ["https://example.com"]

    def test_references_invalid_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            UpdateResearchRequest(references=["not-a-url"])

    def test_references_ftp_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            UpdateResearchRequest(references=["ftp://example.com"])

    # --- Images ---
    def test_images_none_valid(self):
        research = UpdateResearchRequest(images=None)
        assert research.images is None

    def test_images_valid(self):
        research = UpdateResearchRequest(images=["https://example.com/img.png"])
        assert len(research.images) == 1

    def test_images_invalid_raises(self):
        with pytest.raises(ValidationError, match="must start with http"):
            UpdateResearchRequest(images=["ftp://example.com/img.png"])

    # --- Partial updates ---
    def test_partial_update_only_status(self):
        research = UpdateResearchRequest(status=ResearchStatus.completed)
        assert research.status == ResearchStatus.completed
        assert research.title is None
        assert research.tags is None

    def test_partial_update_only_tags(self):
        research = UpdateResearchRequest(tags=["python"])
        assert research.tags == ["python"]
        assert research.title is None
        assert research.status is None

    def test_partial_update_only_title(self):
        research = UpdateResearchRequest(title="New Title")
        assert research.title == "New Title"
        assert research.body is None
        assert research.status is None

    def test_full_update_valid(self):
        research = UpdateResearchRequest(
            title="Updated Title",
            body="Updated body content that is long enough",
            status=ResearchStatus.in_progress,
            category="Science",
            tags=["python", "ai"],
            references=["https://example.com"],
            images=["https://example.com/img.png"],
        )
        assert research.title == "Updated Title"
        assert research.status == ResearchStatus.in_progress
        assert research.tags == ["python", "ai"]