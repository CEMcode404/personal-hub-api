import json
from pydantic import BaseModel, field_validator
from utils.response import success, error, handle_errors


class DummyModel(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def check_name(cls, v):
        if v == "bad":
            raise ValueError("name cannot be 'bad'")
        return v


class TestSuccess:

    def test_default_status_code(self):
        response = success({"id": "1"})
        assert response.status_code == 200

    def test_custom_status_code(self):
        response = success({"id": "1"}, status_code=201)
        assert response.status_code == 201

    def test_body_is_json_encoded(self):
        response = success({"id": "1", "title": "Task"})
        assert json.loads(response.body) == {"id": "1", "title": "Task"}

    def test_content_type_is_json(self):
        response = success({"id": "1"})
        assert response.content_type == "application/json"


class TestError:

    def test_default_status_code(self):
        response = error("Something went wrong")
        assert response.status_code == 400

    def test_custom_status_code(self):
        response = error("Not found", status_code=404)
        assert response.status_code == 404

    def test_body_contains_error_key(self):
        response = error("Something went wrong")
        assert json.loads(response.body) == {"error": "Something went wrong"}


class TestHandleErrors:

    def test_passes_through_successful_call(self):
        @handle_errors
        def fn():
            return success({"ok": True})
        response = fn()
        assert response.status_code == 200

    def test_passes_through_args_and_kwargs(self):
        @handle_errors
        def fn(a, b, c=None):
            return success({"a": a, "b": b, "c": c})
        response = fn(1, 2, c=3)
        assert json.loads(response.body) == {"a": 1, "b": 2, "c": 3}

    def test_catches_custom_validation_error_message(self):
        @handle_errors
        def fn():
            DummyModel(name="bad")
        response = fn()
        assert response.status_code == 422
        assert json.loads(response.body)["error"] == "name cannot be 'bad'"

    def test_strips_value_error_prefix(self):
        @handle_errors
        def fn():
            DummyModel(name="bad")
        response = fn()
        assert "Value error," not in json.loads(response.body)["error"]

    def test_catches_builtin_pydantic_validation_error(self):
        @handle_errors
        def fn():
            DummyModel()  # missing required field
        response = fn()
        assert response.status_code == 422

    def test_catches_value_error(self):
        @handle_errors
        def fn():
            raise ValueError("Todo not found")
        response = fn()
        assert response.status_code == 400
        assert json.loads(response.body)["error"] == "Todo not found"

    def test_catches_generic_exception_returns_500(self):
        @handle_errors
        def fn():
            raise RuntimeError("something broke")
        response = fn()
        assert response.status_code == 500
        assert json.loads(response.body)["error"] == "Internal server error"

    def test_generic_exception_does_not_leak_details(self):
        @handle_errors
        def fn():
            raise RuntimeError("sensitive internal detail")
        response = fn()
        assert "sensitive internal detail" not in response.body

    def test_preserves_function_name_via_wraps(self):
        @handle_errors
        def my_named_function():
            return success({})
        assert my_named_function.__name__ == "my_named_function"