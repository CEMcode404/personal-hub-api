from src.utils.common import clean_internal_fields


class TestCleanInternalFields:

    def test_removes_internal_fields(self):
        result = clean_internal_fields(
            {"id": "1", "gsi_order_sk": "x", "title": "Task"},
            {"gsi_order_sk"}
        )
        assert result == {"id": "1", "title": "Task"}

    def test_removes_multiple_internal_fields(self):
        result = clean_internal_fields(
            {"id": "1", "gsi_order_sk": "x", "status_sk": "y", "title": "Task"},
            {"gsi_order_sk", "status_sk"}
        )
        assert result == {"id": "1", "title": "Task"}

    def test_no_internal_fields_present(self):
        result = clean_internal_fields({"id": "1", "title": "Task"}, {"gsi_order_sk"})
        assert result == {"id": "1", "title": "Task"}

    def test_empty_dict(self):
        assert clean_internal_fields({}, {"gsi_order_sk"}) == {}

    def test_empty_internal_fields_set(self):
        result = clean_internal_fields({"id": "1", "gsi_order_sk": "x"}, set())
        assert result == {"id": "1", "gsi_order_sk": "x"}

    def test_does_not_mutate_original_dict(self):
        original = {"id": "1", "gsi_order_sk": "x"}
        clean_internal_fields(original, {"gsi_order_sk"})
        assert original == {"id": "1", "gsi_order_sk": "x"}

    def test_all_fields_are_internal(self):
        result = clean_internal_fields({"gsi_order_sk": "x", "status_sk": "y"}, {"gsi_order_sk", "status_sk"})
        assert result == {}