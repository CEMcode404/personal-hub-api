import pytest
from pydantic import ValidationError
from src.schemas.todo import CreateTodoRequest, UpdateTodoRequest
from src.constants.todo import TodoStatus, RecurrencePattern


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

    def test_body_strip_and_empty_to_none(self):
        todo = CreateTodoRequest(title="Task", body="   ")
        assert todo.body is None

        todo = CreateTodoRequest(title="Task", body="  hello  ")
        assert todo.body == "hello"
    # Test for the html sanitation

    def test_body_max_length(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(title="Task", body="a" * 2001)

    def test_invalid_datetime_format(self):
        with pytest.raises(ValidationError):
            CreateTodoRequest(title="Task", notify=True, notify_at="not-a-date")

    def test_valid_iso_datetime(self):
        todo = CreateTodoRequest(
            title="Task",
            notify=True,
            notify_at="2026-06-15T10:00:00"
        )
        assert todo.notify_at == "2026-06-15T10:00:00"

    def test_notify_without_notify_at_raises(self):
        with pytest.raises(ValidationError, match="notify_at is required"):
            CreateTodoRequest(title="Task", notify=True)

    def test_notify_with_notify_at_valid(self):
        todo = CreateTodoRequest(
            title="Task",
            notify=True,
            notify_at="2026-06-15T10:00:00"
        )
        assert todo.notify is True
    
    # test notify should be <= recurrence
    # test notify should have a lower limit how earrly it is from the recurrence at
    # test notify at should only be in between the recurrency(monthly) and recurrenc date or prev recurent to new recurrent date
    # notify should not be in past compared to now

    def test_recurring_without_recurrence_and_next_occurrence_raises(self):
        with pytest.raises(ValidationError, match="recurrence and next_occurrence_at are required"):
            CreateTodoRequest(title="Task", is_recurring=True)

    def test_recurring_with_only_recurrence_raises(self):
        with pytest.raises(ValidationError, match="recurrence and next_occurrence_at are required"):
            CreateTodoRequest(
                title="Task",
                is_recurring=True,
                recurrence=RecurrencePattern.daily,
            )

    def test_recurring_with_only_next_occurrence_raises(self):
        with pytest.raises(ValidationError, match="recurrence and next_occurrence_at are required"):
            CreateTodoRequest(
                title="Task",
                is_recurring=True,
                next_occurrence_at="2026-06-16T10:00:00",
            )

    def test_recurring_valid(self):
        todo = CreateTodoRequest(
            title="Task",
            is_recurring=True,
            recurrence=RecurrencePattern.daily,
            next_occurrence_at="2026-06-16T10:00:00",
        )
        assert todo.is_recurring is True
        assert todo.recurrence == RecurrencePattern.daily

    def test_notify_at_after_next_occurrence_raises(self):
        with pytest.raises(ValidationError, match="notify_at must be earlier than or equal to next_occurrence_at"):
            CreateTodoRequest(
                title="Task",
                is_recurring=True,
                recurrence=RecurrencePattern.daily,
                next_occurrence_at="2026-06-16T10:00:00",
                notify=True,
                notify_at="2026-06-17T10:00:00",
            )

    def test_notify_at_equal_to_next_occurrence_valid(self):
        todo = CreateTodoRequest(
            title="Task",
            is_recurring=True,
            recurrence=RecurrencePattern.daily,
            next_occurrence_at="2026-06-16T10:00:00",
            notify=True,
            notify_at="2026-06-16T10:00:00",
        )
        assert todo.notify_at == todo.next_occurrence_at

    def test_notify_at_before_next_occurrence_valid(self):
        todo = CreateTodoRequest(
            title="Task",
            is_recurring=True,
            recurrence=RecurrencePattern.daily,
            next_occurrence_at="2026-06-16T10:00:00",
            notify=True,
            notify_at="2026-06-15T10:00:00",
        )
        assert todo.notify_at < todo.next_occurrence_at

    # recurrenece should not be in the passed
    # recurrence should not be > 2 years
    # recurrent pattern should be one in the enum


class TestUpdateTodoRequest:
    # apply the same missing test from the createtodorequest
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
        # title=None is fine, but empty string is not
        todo = UpdateTodoRequest(title=None)
        assert todo.title is None

    def test_body_strip_and_empty_to_none(self):
        todo = UpdateTodoRequest(body="   ")
        assert todo.body is None

    def test_status_update(self):
        todo = UpdateTodoRequest(status=TodoStatus.completed)
        assert todo.status == TodoStatus.completed

    def test_invalid_datetime_format(self):
        with pytest.raises(ValidationError):
            UpdateTodoRequest(notify_at="invalid-date")

    def test_notify_without_notify_at_raises(self):
        with pytest.raises(ValidationError, match="notify_at is required"):
            UpdateTodoRequest(notify=True)

    def test_recurring_without_required_fields_raises(self):
        with pytest.raises(ValidationError, match="recurrence and next_occurrence_at are required"):
            UpdateTodoRequest(is_recurring=True)

    def test_recurring_valid(self):
        todo = UpdateTodoRequest(
            is_recurring=True,
            recurrence=RecurrencePattern.weekly,
            next_occurrence_at="2026-06-22T10:00:00",
        )
        assert todo.recurrence == RecurrencePattern.weekly

    def test_notify_at_after_next_occurrence_raises(self):
        with pytest.raises(ValidationError, match="notify_at must be earlier than or equal to next_occurrence_at"):
            UpdateTodoRequest(
                is_recurring=True,
                recurrence=RecurrencePattern.daily,
                next_occurrence_at="2026-06-16T10:00:00",
                notify=True,
                notify_at="2026-06-17T10:00:00",
            )

    def test_partial_update_only_title(self):
        todo = UpdateTodoRequest(title="New Title")
        assert todo.title == "New Title"
        assert todo.body is None
        assert todo.status is None