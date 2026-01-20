"""Tests for LazarusAdapter."""

from typing import Any, ClassVar

from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.lazarus import LazarusAdapter, adapt_expert
from chuk_virtual_expert.models import VirtualExpertAction


class MockTimeExpert(VirtualExpert):
    """Mock time expert for testing the adapter."""

    name: ClassVar[str] = "time"
    description: ClassVar[str] = "Time operations"
    priority: ClassVar[int] = 5

    def get_operations(self) -> list[str]:
        return ["get_time", "convert_time"]

    def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
        if op == "get_time":
            tz = params.get("timezone", "UTC")
            return {
                "query_type": "current_time",
                "timezone": tz,
                "formatted": "2024-01-01 12:00:00",
            }
        elif op == "convert_time":
            return {
                "query_type": "conversion",
                "from_time": params.get("time", ""),
                "from_timezone": params.get("from_timezone", ""),
                "to_time": "12:00",
                "to_timezone": params.get("to_timezone", ""),
            }
        else:
            return {"query_type": "error", "error": f"Unknown op: {op}"}


class MockGenericExpert(VirtualExpert):
    """Mock non-time expert for testing."""

    name: ClassVar[str] = "generic"
    description: ClassVar[str] = "Generic operations"
    priority: ClassVar[int] = 3

    def get_operations(self) -> list[str]:
        return ["do_something"]

    def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"result": "done"}


class TestLazarusAdapterCreation:
    """Tests for adapter creation."""

    def test_creation(self):
        expert = MockTimeExpert()
        adapter = LazarusAdapter(expert)
        assert adapter._expert is expert

    def test_adapt_expert_function(self):
        expert = MockTimeExpert()
        adapter = adapt_expert(expert)
        assert isinstance(adapter, LazarusAdapter)


class TestLazarusAdapterProperties:
    """Tests for adapter properties."""

    def test_name(self):
        adapter = LazarusAdapter(MockTimeExpert())
        assert adapter.name == "time"

    def test_description(self):
        adapter = LazarusAdapter(MockTimeExpert())
        assert adapter.description == "Time operations"

    def test_priority(self):
        adapter = LazarusAdapter(MockTimeExpert())
        assert adapter.priority == 5


class TestCanHandle:
    """Tests for can_handle method."""

    def test_handles_time_keyword(self):
        adapter = LazarusAdapter(MockTimeExpert())
        assert adapter.can_handle("What time is it?")

    def test_handles_timezone_keyword(self):
        adapter = LazarusAdapter(MockTimeExpert())
        assert adapter.can_handle("What timezone is Tokyo in?")

    def test_handles_utc_keyword(self):
        adapter = LazarusAdapter(MockTimeExpert())
        assert adapter.can_handle("Get UTC time")

    def test_rejects_unrelated_query(self):
        adapter = LazarusAdapter(MockTimeExpert())
        assert not adapter.can_handle("Tell me a joke")

    def test_generic_expert_uses_operations(self):
        adapter = LazarusAdapter(MockGenericExpert())
        # Should use operation names as keywords
        assert adapter.can_handle("do_something here")


class TestExecute:
    """Tests for execute method."""

    def test_execute_utc_time(self):
        adapter = LazarusAdapter(MockTimeExpert())
        result = adapter.execute("What time is it?")
        assert "12:00:00" in result
        assert "UTC" in result

    def test_execute_timezone_time(self):
        adapter = LazarusAdapter(MockTimeExpert())
        result = adapter.execute("What time is it in Tokyo?")
        assert result is not None

    def test_execute_returns_string(self):
        adapter = LazarusAdapter(MockTimeExpert())
        result = adapter.execute("What time is it?")
        assert isinstance(result, str)


class TestExecuteAction:
    """Tests for execute_action method (CoT interface)."""

    def test_execute_with_pydantic_action(self):
        adapter = LazarusAdapter(MockTimeExpert())
        action = VirtualExpertAction(
            expert="time",
            operation="get_time",
            parameters={"timezone": "Asia/Tokyo"},
        )
        result = adapter.execute_action(action)
        assert result is not None
        assert isinstance(result, str)

    def test_execute_with_mock_lazarus_action(self):
        adapter = LazarusAdapter(MockTimeExpert())

        # Simulate a Lazarus dataclass-style action
        class MockLazarusAction:
            expert = "time"
            operation = "get_time"
            parameters = {"timezone": "UTC"}
            confidence = 1.0
            reasoning = "Test"

            def to_json(self):
                return '{"expert": "time"}'

        action = MockLazarusAction()
        result = adapter.execute_action(action)
        assert result is not None

    def test_execute_action_error_handling(self):
        adapter = LazarusAdapter(MockTimeExpert())
        action = VirtualExpertAction(
            expert="time",
            operation="unknown_operation",
        )
        result = adapter.execute_action(action)
        # Should return error message
        assert result is None or "Error" in str(result)


class TestGetCalibrationPrompts:
    """Tests for get_calibration_prompts method (legacy)."""

    def test_returns_tuple(self):
        adapter = LazarusAdapter(MockTimeExpert())
        result = adapter.get_calibration_prompts()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_lists(self):
        adapter = LazarusAdapter(MockTimeExpert())
        positive, negative = adapter.get_calibration_prompts()
        assert isinstance(positive, list)
        assert isinstance(negative, list)


class TestGetCalibrationActions:
    """Tests for get_calibration_actions method (CoT interface)."""

    def test_returns_tuple(self):
        adapter = LazarusAdapter(MockTimeExpert())
        result = adapter.get_calibration_actions()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_same_as_calibration_prompts(self):
        adapter = LazarusAdapter(MockTimeExpert())
        actions = adapter.get_calibration_actions()
        prompts = adapter.get_calibration_prompts()
        # Should return the same data
        assert actions == prompts


class TestGetCotExamples:
    """Tests for get_cot_examples method."""

    def test_returns_list(self):
        adapter = LazarusAdapter(MockTimeExpert())
        examples = adapter.get_cot_examples()
        assert isinstance(examples, list)

    def test_examples_have_query_and_action(self):
        adapter = LazarusAdapter(MockTimeExpert())
        examples = adapter.get_cot_examples()
        # May be empty if no cot_examples.json exists
        for ex in examples:
            assert "query" in ex
            assert "action" in ex


class TestFormatResult:
    """Tests for _format_result method."""

    def test_format_current_time(self):
        adapter = LazarusAdapter(MockTimeExpert())
        data = {
            "query_type": "current_time",
            "timezone": "UTC",
            "formatted": "2024-01-01 12:00:00",
        }
        result = adapter._format_result(data)
        assert "12:00:00" in result
        assert "UTC" in result

    def test_format_conversion(self):
        adapter = LazarusAdapter(MockTimeExpert())
        data = {
            "query_type": "conversion",
            "from_time": "3:00 PM",
            "from_timezone": "EST",
            "to_time": "12:00 PM",
            "to_timezone": "PST",
        }
        result = adapter._format_result(data)
        assert "EST" in result
        assert "PST" in result

    def test_format_timezone_info(self):
        adapter = LazarusAdapter(MockTimeExpert())
        data = {
            "query_type": "timezone_info",
            "location": "Tokyo",
            "iana_timezone": "Asia/Tokyo",
        }
        result = adapter._format_result(data)
        assert "Tokyo" in result
        assert "Asia/Tokyo" in result

    def test_format_error(self):
        adapter = LazarusAdapter(MockTimeExpert())
        data = {
            "query_type": "error",
            "error": "Something went wrong",
        }
        result = adapter._format_result(data)
        assert "Error" in result or "wrong" in result

    def test_format_fallback_json(self):
        adapter = LazarusAdapter(MockTimeExpert())
        data = {
            "query_type": "unknown_type",
            "some_field": "some_value",
        }
        result = adapter._format_result(data)
        # Should return JSON as fallback
        assert "unknown_type" in result or "some_value" in result


class TestRepr:
    """Tests for __repr__ method."""

    def test_repr(self):
        adapter = LazarusAdapter(MockTimeExpert())
        repr_str = repr(adapter)
        assert "LazarusAdapter" in repr_str
        assert "MockTimeExpert" in repr_str
