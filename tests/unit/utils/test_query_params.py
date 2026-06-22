from utils.query_params import parse_int, parse_cursor, parse_str


class TestParseInt:

    def test_valid_int_string(self):
        assert parse_int("50") == 50

    def test_valid_int(self):
        assert parse_int(50) == 50

    def test_clamps_above_max(self):
        assert parse_int("500", max_val=100) == 100

    def test_clamps_below_min(self):
        assert parse_int("-5", min_val=1) == 1

    def test_invalid_string_returns_default(self):
        assert parse_int("abc", default=10) == 10

    def test_none_returns_default(self):
        assert parse_int(None, default=10) == 10

    def test_float_string_returns_default(self):
        assert parse_int("10.5", default=10) == 10

    def test_custom_default_min_max(self):
        assert parse_int("abc", default=25, min_val=5, max_val=50) == 25

    def test_exact_boundary_min(self):
        assert parse_int(1, min_val=1, max_val=100) == 1

    def test_exact_boundary_max(self):
        assert parse_int(100, min_val=1, max_val=100) == 100

    def test_uses_default_min_max_values(self):
        assert parse_int("50") == 50
        assert parse_int("0") == 1
        assert parse_int("200") == 100


class TestParseCursor:

    def test_valid_json_object(self):
        assert parse_cursor('{"id": "123"}') == {"id": "123"}

    def test_none_returns_none(self):
        assert parse_cursor(None) is None

    def test_empty_string_returns_none(self):
        assert parse_cursor("") is None

    def test_invalid_json_returns_none(self):
        assert parse_cursor("not-json") is None

    def test_valid_json_array(self):
        assert parse_cursor('[1, 2, 3]') == [1, 2, 3]

    def test_valid_json_nested(self):
        assert parse_cursor('{"a": {"b": 1}}') == {"a": {"b": 1}}


class TestParseStr:

    def test_valid_string(self):
        assert parse_str("hello") == "hello"

    def test_strips_whitespace(self):
        assert parse_str("  hello  ") == "hello"

    def test_none_returns_default(self):
        assert parse_str(None) is None

    def test_empty_string_returns_default(self):
        assert parse_str("") is None

    def test_custom_default(self):
        assert parse_str(None, default="fallback") == "fallback"

    def test_non_string_input_converted(self):
        assert parse_str(123) == "123"

    def test_whitespace_only_returns_empty_string_not_default(self):
        # whitespace is truthy, so it passes through as stripped "" rather than default
        assert parse_str("   ") == ""