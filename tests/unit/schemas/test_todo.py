import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from src.schemas.todo import CreateTodoRequest, UpdateTodoRequest
from src.constants.todo import TodoStatus, RecurrencePattern


def future(days=1):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def past(days=1):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


class TestCreateTodoRequest:
    def test_minimal_valid(self):
        todo = CreateTodoRequest(title="Buy milk")
        assert todo.title == "Buy milk"
        assert todo.body is None
        assert todo.is_recurring is False
        assert todo.notify is False

    def test_title_required(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest()

    def test_title_strip_whitespace(self):
        todo = CreateTodoRequest(title="  Buy milk  ")
        assert todo.title == "Buy milk"

    def test_title_empty_after_strip_raises(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(title="   ")

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(title="a" * 256)

    def test_title_strips_html(self):
        todo = CreateTodoRequest(title="<script>alert(1)</script>Buy milk")
        assert "<script>" not in todo.title
        assert "Buy milk" in todo.title

    def test_title_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(title="<script>alert(1)</script>")

    def test_body_strip_and_empty_to_none(self):
        todo = CreateTodoRequest(title="Task", body="   ")
        assert todo.body is None

        todo = CreateTodoRequest(title="Task", body="  hello  ")
        assert todo.body == "hello"

    def test_body_max_length(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(title="Task", body="a" * 2001)

    def test_body_strips_html(self):
        todo = CreateTodoRequest(title="Task", body="<script>alert(1)</script>Buy milk")
        assert "<script>" not in todo.body
        assert "Buy milk" in todo.body

    def test_invalid_datetime_format(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(title="Task", notify=True, notify_at="not-a-date")

    def test_valid_iso_datetime(self):
        notify_at = future(1)
        todo = CreateTodoRequest(title="Task", notify=True, notify_at=notify_at)
        assert todo.notify_at == notify_at

    def test_notify_without_notify_at_raises(self):
        with pytest.raises(ValidationError, match="notify_at is required"):
            CreateTodoRequest(title="Task", notify=True)

    def test_notify_with_notify_at_valid(self):
        todo = CreateTodoRequest(title="Task", notify=True, notify_at=future(1))
        assert todo.notify is True

    def test_notify_at_in_past_raises(self):
        with pytest.raises(ValidationError, match="notify_at cannot be in the past"):
            CreateTodoRequest(title="Task", notify=True, notify_at=past(1))

    def test_notify_at_at_exact_now_boundary_valid(self):
        almost_now = (datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat()
        todo = CreateTodoRequest(title="Task", notify=True, notify_at=almost_now)
        assert todo.notify_at == almost_now

    def test_notify_at_naive_datetime_in_past_raises(self):
        naive_past = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None).isoformat()
        with pytest.raises(ValidationError, match="notify_at cannot be in the past"):
            CreateTodoRequest(title="Task", notify=True, notify_at=naive_past)

    def test_recurring_without_recurrence_and_next_occurrence_raises(self):
        with pytest.raises(ValidationError, match="recurrence and next_occurrence_at are required"):
            CreateTodoRequest(title="Task", is_recurring=True)

    def test_invalid_next_occurrence_datetime_format(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(
                title="Task", is_recurring=True,
                recurrence=RecurrencePattern.daily, next_occurrence_at="not-a-date"
            )

    def test_invalid_next_occurrence_datetime_format(self):
        with pytest.raises(ValidationError):
            UpdateTodoRequest(next_occurrence_at="not-a-date")

    def test_recurring_with_only_recurrence_raises(self):
        with pytest.raises(ValidationError, match="recurrence and next_occurrence_at are required"):
            CreateTodoRequest(title="Task", is_recurring=True, recurrence=RecurrencePattern.daily)

    def test_recurring_with_only_next_occurrence_raises(self):
        with pytest.raises(ValidationError, match="recurrence and next_occurrence_at are required"):
            CreateTodoRequest(title="Task", is_recurring=True, next_occurrence_at=future(1))

    def test_recurring_valid(self):
        next_at = future(1)
        todo = CreateTodoRequest(
            title="Task",
            is_recurring=True,
            recurrence=RecurrencePattern.daily,
            next_occurrence_at=next_at,
        )
        assert todo.is_recurring is True
        assert todo.recurrence == RecurrencePattern.daily

    def test_recurrence_invalid_enum_value_raises(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(
                title="Task",
                is_recurring=True,
                recurrence="not_a_real_pattern",
                next_occurrence_at=future(1),
            )

    def test_next_occurrence_in_past_raises(self):
        with pytest.raises(ValidationError, match="next_occurrence_at cannot be in the past"):
            CreateTodoRequest(
                title="Task",
                is_recurring=True,
                recurrence=RecurrencePattern.daily,
                next_occurrence_at=past(1),
            )

    def test_next_occurrence_naive_datetime_in_past_raises(self):
        naive_past = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None).isoformat()
        with pytest.raises(ValidationError, match="next_occurrence_at cannot be in the past"):
            CreateTodoRequest(
                title="Task", is_recurring=True,
                recurrence=RecurrencePattern.daily, next_occurrence_at=naive_past
            )

    def test_next_occurrence_beyond_two_years_raises(self):
        with pytest.raises(ValidationError, match="cannot be more than 2 years"):
            CreateTodoRequest(
                title="Task",
                is_recurring=True,
                recurrence=RecurrencePattern.daily,
                next_occurrence_at=future(731),
            )

    def test_next_occurrence_within_two_years_valid(self):
        todo = CreateTodoRequest(
            title="Task",
            is_recurring=True,
            recurrence=RecurrencePattern.daily,
            next_occurrence_at=future(729),
        )
        assert todo.next_occurrence_at is not None

    def test_notify_at_after_next_occurrence_raises(self):
        next_at = future(2)
        notify_at = future(3)
        with pytest.raises(ValidationError, match="notify_at must be earlier than or equal to next_occurrence_at"):
            CreateTodoRequest(
                title="Task",
                is_recurring=True,
                recurrence=RecurrencePattern.daily,
                next_occurrence_at=next_at,
                notify=True,
                notify_at=notify_at,
            )

    def test_notify_at_equal_to_next_occurrence_valid(self):
        same_time = future(2)
        todo = CreateTodoRequest(
            title="Task",
            is_recurring=True,
            recurrence=RecurrencePattern.daily,
            next_occurrence_at=same_time,
            notify=True,
            notify_at=same_time,
        )
        assert todo.notify_at == todo.next_occurrence_at

    def test_notify_at_before_next_occurrence_valid(self):
        todo = CreateTodoRequest(
            title="Task",
            is_recurring=True,
            recurrence=RecurrencePattern.daily,
            next_occurrence_at=future(3),
            notify=True,
            notify_at=future(1),
        )
        assert todo.notify_at < todo.next_occurrence_at

    def test_ordering_check_uses_datetime_not_string_comparison(self):
        with pytest.raises(ValidationError, match="notify_at must be earlier than or equal to next_occurrence_at"):
            CreateTodoRequest(
                title="Task",
                is_recurring=True,
                recurrence=RecurrencePattern.monthly,
                next_occurrence_at=future(1),
                notify=True,
                notify_at=future(5),
            )

    def test_mixed_naive_and_aware_datetimes_compared_correctly(self):
        next_at_naive = (datetime.now(timezone.utc) + timedelta(days=2)).replace(tzinfo=None).isoformat()
        notify_at_aware = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        todo = CreateTodoRequest(
            title="Task",
            is_recurring=True,
            recurrence=RecurrencePattern.daily,
            next_occurrence_at=next_at_naive,
            notify=True,
            notify_at=notify_at_aware,
        )
        assert todo.notify is True


class TestUpdateTodoRequest:
    def test_all_fields_optional(self):
        todo = UpdateTodoRequest()
        assert todo.title is None
        assert todo.status is None

    def test_title_strip_whitespace(self):
        todo = UpdateTodoRequest(title="  Updated  ")
        assert todo.title == "Updated"

    def test_title_empty_after_strip_raises(self):
        with pytest.raises(ValidationError):
            UpdateTodoRequest(title="   ")

    def test_title_min_length_when_provided(self):
        todo = UpdateTodoRequest(title=None)
        assert todo.title is None

    def test_title_strips_html(self):
        todo = UpdateTodoRequest(title="<script>alert(1)</script>Updated")
        assert "<script>" not in todo.title
        assert "Updated" in todo.title

    def test_title_pure_html_raises_after_sanitize(self):
        with pytest.raises(ValidationError):
            UpdateTodoRequest(title="<script>alert(1)</script>")

    def test_body_strip_and_empty_to_none(self):
        todo = UpdateTodoRequest(body="   ")
        assert todo.body is None

    def test_body_strips_html(self):
        todo = UpdateTodoRequest(body="<script>alert(1)</script>Updated")
        assert "<script>" not in todo.body
        assert "Updated" in todo.body

    def test_status_update(self):
        todo = UpdateTodoRequest(status=TodoStatus.completed)
        assert todo.status == TodoStatus.completed

    def test_invalid_datetime_format(self):
        with pytest.raises(ValidationError):
            UpdateTodoRequest(notify_at="invalid-date")

    def test_notify_without_notify_at_raises(self):
        with pytest.raises(ValidationError, match="notify_at is required"):
            UpdateTodoRequest(notify=True)

    def test_notify_at_in_past_raises(self):
        with pytest.raises(ValidationError, match="notify_at cannot be in the past"):
            UpdateTodoRequest(notify=True, notify_at=past(1))

    def test_recurring_without_required_fields_raises(self):
        with pytest.raises(ValidationError, match="recurrence and next_occurrence_at are required"):
            UpdateTodoRequest(is_recurring=True)

    def test_recurring_valid(self):
        todo = UpdateTodoRequest(
            is_recurring=True,
            recurrence=RecurrencePattern.weekly,
            next_occurrence_at=future(7),
        )
        assert todo.recurrence == RecurrencePattern.weekly

    def test_recurrence_invalid_enum_value_raises(self):
        with pytest.raises(ValidationError):
            UpdateTodoRequest(
                is_recurring=True,
                recurrence="not_a_real_pattern",
                next_occurrence_at=future(1),
            )

    def test_notify_at_naive_datetime_in_past_raises(self):
        naive_past = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None).isoformat()
        with pytest.raises(ValidationError, match="notify_at cannot be in the past"):
            UpdateTodoRequest(notify=True, notify_at=naive_past)


    def test_invalid_next_occurrence_datetime_format(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(title="Task", is_recurring=True, recurrence=RecurrencePattern.daily, next_occurrence_at="not-a-date")


    def test_next_occurrence_in_past_raises(self):
        with pytest.raises(ValidationError, match="next_occurrence_at cannot be in the past"):
            UpdateTodoRequest(
                is_recurring=True,
                recurrence=RecurrencePattern.daily,
                next_occurrence_at=past(1),
            )

    def test_next_occurrence_beyond_two_years_raises(self):
        with pytest.raises(ValidationError, match="cannot be more than 2 years"):
            UpdateTodoRequest(
                is_recurring=True,
                recurrence=RecurrencePattern.daily,
                next_occurrence_at=future(731),
            )

    def test_notify_at_after_next_occurrence_raises(self):
        with pytest.raises(ValidationError, match="notify_at must be earlier than or equal to next_occurrence_at"):
            UpdateTodoRequest(
                is_recurring=True,
                recurrence=RecurrencePattern.daily,
                next_occurrence_at=future(2),
                notify=True,
                notify_at=future(3),
            )

    def test_partial_update_only_title(self):
        todo = UpdateTodoRequest(title="New Title")
        assert todo.title == "New Title"
        assert todo.body is None
        assert todo.status is None