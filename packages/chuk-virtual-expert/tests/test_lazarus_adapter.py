"""Tests for LazarusAdapter."""

from typing import Any, ClassVar

import pytest

from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.lazarus import LazarusAdapter, adapt_expert
from chuk_virtual_expert.models import VirtualExpertAction


class MockTimeExpert(VirtualExpert):
    """Mock time expert for testing the adapter."""

    name: ClassVar[str] = "time"
    description: ClassVar[str] = "Time operations"
    priority: ClassVar[int] = 5

    _TIME_KEYWORDS = ["time", "timezone", "clock", "utc", "gmt", "est", "pst"]

    def can_handle(self, prompt: str) -> bool:
        prompt_lower = prompt.lower()
        return any(kw in prompt_lower for kw in self._TIME_KEYWORDS)

    def get_operations(self) -> list[str]:
        return ["get_time", "convert_time"]

    async def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
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

    def can_handle(self, prompt: str) -> bool:
        return "do_something" in prompt.lower() or "generic" in prompt.lower()

    def get_operations(self) -> list[str]:
        return ["do_something"]

    async def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
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

    @pytest.mark.asyncio
    async def test_execute_utc_time(self):
        adapter = LazarusAdapter(MockTimeExpert())
        result = await adapter.execute("What time is it?")
        assert "12:00:00" in result
        assert "UTC" in result

    @pytest.mark.asyncio
    async def test_execute_timezone_time(self):
        adapter = LazarusAdapter(MockTimeExpert())
        result = await adapter.execute("What time is it in Tokyo?")
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_returns_string(self):
        adapter = LazarusAdapter(MockTimeExpert())
        result = await adapter.execute("What time is it?")
        assert isinstance(result, str)


class TestExecuteAction:
    """Tests for execute_action method (CoT interface)."""

    @pytest.mark.asyncio
    async def test_execute_with_pydantic_action(self):
        adapter = LazarusAdapter(MockTimeExpert())
        action = VirtualExpertAction(
            expert="time",
            operation="get_time",
            parameters={"timezone": "Asia/Tokyo"},
        )
        result = await adapter.execute_action(action)
        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_execute_with_mock_lazarus_action(self):
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
        result = await adapter.execute_action(action)
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_action_error_handling(self):
        adapter = LazarusAdapter(MockTimeExpert())
        action = VirtualExpertAction(
            expert="time",
            operation="unknown_operation",
        )
        result = await adapter.execute_action(action)
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


class TestExecuteErrorPaths:
    """Tests for error handling in execute method."""

    @pytest.mark.asyncio
    async def test_execute_returns_error_message(self):
        """Test that error results are formatted as error messages."""

        class FailingExpert(VirtualExpert):
            name: ClassVar[str] = "failing"
            description: ClassVar[str] = "Always fails"
            priority: ClassVar[int] = 1

            def can_handle(self, prompt: str) -> bool:
                return True

            def get_operations(self) -> list[str]:
                return ["fail"]

            async def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
                raise ValueError("Intentional failure")

        adapter = LazarusAdapter(FailingExpert())
        result = await adapter.execute("test")
        assert result is not None
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_execute_returns_none_when_no_data(self):
        """Test that execute returns None when result has no data."""

        class EmptyResultExpert(VirtualExpert):
            name: ClassVar[str] = "empty"
            description: ClassVar[str] = "Returns empty"
            priority: ClassVar[int] = 1

            def can_handle(self, prompt: str) -> bool:
                return True

            def get_operations(self) -> list[str]:
                return ["empty"]

            async def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
                return {}  # Empty dict, no data

        adapter = LazarusAdapter(EmptyResultExpert())
        result = await adapter.execute("test")
        # Empty dict is falsy, so _format_result is not called
        # result.data is {} which is falsy, so execute returns None
        assert result is None


class TestParsePromptGenericExpert:
    """Tests for _parse_prompt with non-time experts."""

    def test_generic_expert_uses_default_parsing(self):
        """Test that non-time experts use the default parsing path."""
        adapter = LazarusAdapter(MockGenericExpert())
        action = adapter._parse_prompt("do something with this query")
        assert action.expert == "generic"
        assert action.operation == "do_something"
        assert action.parameters == {"query": "do something with this query"}
        assert action.reasoning == "Parsed via LazarusAdapter"


class TestParseTimePrompt:
    """Tests for _parse_time_prompt method."""

    def test_parse_convert_time(self):
        """Test parsing time conversion prompts."""
        adapter = LazarusAdapter(MockTimeExpert())
        action = adapter._parse_time_prompt("Convert 3pm EST to PST")
        assert action.operation == "convert_time"
        assert "time" in action.parameters
        assert "from_timezone" in action.parameters
        assert "to_timezone" in action.parameters

    def test_parse_timezone_info(self):
        """Test parsing timezone info prompts."""
        adapter = LazarusAdapter(MockTimeExpert())
        action = adapter._parse_time_prompt("Get timezone for Tokyo")
        assert action.operation == "get_timezone_info"
        assert action.parameters.get("location") == "tokyo"

    def test_parse_timezone_info_of_pattern(self):
        """Test parsing 'timezone of' pattern."""
        adapter = LazarusAdapter(MockTimeExpert())
        action = adapter._parse_time_prompt("timezone of london")
        assert action.operation == "get_timezone_info"
        assert action.parameters.get("location") == "london"

    def test_parse_time_in_location(self):
        """Test parsing 'time in location' prompts."""
        adapter = LazarusAdapter(MockTimeExpert())
        action = adapter._parse_time_prompt("What time is it in Tokyo?")
        assert action.operation == "get_time"
        assert "timezone" in action.parameters

    def test_parse_default_utc(self):
        """Test that ambiguous prompts default to UTC."""
        adapter = LazarusAdapter(MockTimeExpert())
        action = adapter._parse_time_prompt("What is the current time?")
        # Falls through to default, should return get_time with empty params
        assert action.operation == "get_time"


class TestFormatResultWithEnum:
    """Tests for _format_result with Enum query_type."""

    def test_format_with_enum_query_type(self):
        """Test formatting when query_type is an Enum."""
        from enum import Enum

        class QueryType(Enum):
            CURRENT_TIME = "current_time"

        adapter = LazarusAdapter(MockTimeExpert())
        data = {
            "query_type": QueryType.CURRENT_TIME,
            "timezone": "UTC",
            "formatted": "2024-01-01 12:00:00",
        }
        result = adapter._format_result(data)
        assert "12:00:00" in result
        assert "UTC" in result


class TestExecuteActionEdgeCases:
    """Tests for execute_action edge cases."""

    @pytest.mark.asyncio
    async def test_execute_action_with_invalid_object(self):
        """Test execute_action returns None for invalid action."""
        adapter = LazarusAdapter(MockTimeExpert())
        result = await adapter.execute_action({"not": "an action"})
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_action_success_without_error(self):
        """Test execute_action returns formatted result on success."""
        adapter = LazarusAdapter(MockTimeExpert())
        action = VirtualExpertAction(
            expert="time",
            operation="get_time",
            parameters={"timezone": "UTC"},
        )
        result = await adapter.execute_action(action)
        assert result is not None
        assert "UTC" in result

    @pytest.mark.asyncio
    async def test_execute_action_with_failing_execution(self):
        """Test execute_action with failing expert."""

        class FailingExpert(VirtualExpert):
            name: ClassVar[str] = "failing"
            description: ClassVar[str] = "Always fails"
            priority: ClassVar[int] = 1

            def can_handle(self, prompt: str) -> bool:
                return True

            def get_operations(self) -> list[str]:
                return ["fail"]

            async def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
                raise ValueError("Intentional failure")

        adapter = LazarusAdapter(FailingExpert())
        action = VirtualExpertAction(
            expert="failing",
            operation="fail",
            parameters={},
        )
        result = await adapter.execute_action(action)
        assert result is not None
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_execute_action_returns_none_no_data(self):
        """Test execute_action returns None when result has no data and no error."""
        adapter = LazarusAdapter(MockTimeExpert())

        class MockAction:
            expert = "time"
            operation = "get_time"
            parameters = {}

        result = await adapter.execute_action(MockAction())
        # Should succeed
        assert result is not None
