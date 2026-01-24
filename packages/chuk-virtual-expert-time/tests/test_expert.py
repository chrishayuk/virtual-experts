"""Tests for TimeExpert class."""

import pytest
from chuk_virtual_expert.models import VirtualExpertAction, VirtualExpertResult

from chuk_virtual_expert_time.expert import (
    TIMEZONE_ALIASES,
    AccuracyMode,
    TimeExpert,
    TimeMCPTool,
    TimeOperation,
    TimeQueryType,
)


class TestTimeOperation:
    """Tests for TimeOperation enum."""

    def test_get_time_value(self):
        assert TimeOperation.GET_TIME == "get_time"
        assert TimeOperation.GET_TIME.value == "get_time"

    def test_convert_time_value(self):
        assert TimeOperation.CONVERT_TIME == "convert_time"

    def test_get_timezone_info_value(self):
        assert TimeOperation.GET_TIMEZONE_INFO == "get_timezone_info"


class TestTimeMCPTool:
    """Tests for TimeMCPTool enum."""

    def test_tool_names(self):
        assert TimeMCPTool.GET_LOCAL_TIME == "get_local_time"
        assert TimeMCPTool.CONVERT_TIME == "convert_time"
        assert TimeMCPTool.GET_TIMEZONE_INFO == "get_timezone_info"


class TestAccuracyMode:
    """Tests for AccuracyMode enum."""

    def test_values(self):
        assert AccuracyMode.FAST == "fast"
        assert AccuracyMode.ACCURATE == "accurate"


class TestTimeQueryType:
    """Tests for TimeQueryType enum."""

    def test_values(self):
        assert TimeQueryType.CURRENT_TIME == "current_time"
        assert TimeQueryType.CONVERSION == "conversion"
        assert TimeQueryType.TIMEZONE_INFO == "timezone_info"
        assert TimeQueryType.ERROR == "error"


class TestTimezoneAliases:
    """Tests for TIMEZONE_ALIASES constant."""

    def test_cities(self):
        assert TIMEZONE_ALIASES["tokyo"] == "Asia/Tokyo"
        assert TIMEZONE_ALIASES["london"] == "Europe/London"
        assert TIMEZONE_ALIASES["new york"] == "America/New_York"

    def test_abbreviations(self):
        assert TIMEZONE_ALIASES["est"] == "America/New_York"
        assert TIMEZONE_ALIASES["pst"] == "America/Los_Angeles"
        assert TIMEZONE_ALIASES["jst"] == "Asia/Tokyo"


class TestTimeExpertCreation:
    """Tests for TimeExpert creation."""

    def test_default_creation(self):
        expert = TimeExpert()
        assert expert is not None

    def test_mcp_server_url(self):
        expert = TimeExpert()
        assert expert.mcp_server_url == "https://time.chukai.io/mcp"


class TestTimeExpertClassAttributes:
    """Tests for TimeExpert class attributes."""

    def test_name(self):
        expert = TimeExpert()
        assert expert.name == "time"

    def test_description(self):
        expert = TimeExpert()
        assert "time" in expert.description.lower()

    def test_version(self):
        expert = TimeExpert()
        assert expert.version == "3.0.0"

    def test_priority(self):
        expert = TimeExpert()
        assert expert.priority == 5


class TestGetOperations:
    """Tests for get_operations method."""

    def test_returns_list(self):
        expert = TimeExpert()
        ops = expert.get_operations()
        assert isinstance(ops, list)

    def test_contains_all_operations(self):
        expert = TimeExpert()
        ops = expert.get_operations()
        assert "get_time" in ops
        assert "convert_time" in ops
        assert "get_timezone_info" in ops


class TestGetMcpToolName:
    """Tests for get_mcp_tool_name method."""

    def test_get_time_maps_to_get_local_time(self):
        expert = TimeExpert()
        tool = expert.get_mcp_tool_name(TimeOperation.GET_TIME.value)
        assert tool == TimeMCPTool.GET_LOCAL_TIME.value

    def test_convert_time_maps_to_convert_time(self):
        expert = TimeExpert()
        tool = expert.get_mcp_tool_name(TimeOperation.CONVERT_TIME.value)
        assert tool == TimeMCPTool.CONVERT_TIME.value

    def test_get_timezone_info_maps_correctly(self):
        expert = TimeExpert()
        tool = expert.get_mcp_tool_name(TimeOperation.GET_TIMEZONE_INFO.value)
        assert tool == TimeMCPTool.GET_TIMEZONE_INFO.value

    def test_unknown_operation_raises(self):
        expert = TimeExpert()
        with pytest.raises(ValueError):
            expert.get_mcp_tool_name("unknown_op")


class TestTransformParameters:
    """Tests for transform_parameters method."""

    def test_get_time_resolves_alias(self):
        expert = TimeExpert()
        params = expert.transform_parameters(
            TimeOperation.GET_TIME.value,
            {"timezone": "tokyo"},
        )
        assert params["timezone"] == "Asia/Tokyo"
        assert params["mode"] == AccuracyMode.FAST.value

    def test_convert_time_maps_parameters(self):
        expert = TimeExpert()
        params = expert.transform_parameters(
            TimeOperation.CONVERT_TIME.value,
            {"time": "2024-01-15T09:00:00", "from_timezone": "est", "to_timezone": "pst"},
        )
        assert params["datetime_str"] == "2024-01-15T09:00:00"
        assert params["from_timezone"] == "America/New_York"
        assert params["to_timezone"] == "America/Los_Angeles"

    def test_get_timezone_info_resolves_location(self):
        expert = TimeExpert()
        params = expert.transform_parameters(
            TimeOperation.GET_TIMEZONE_INFO.value,
            {"location": "sydney"},
        )
        assert params["timezone"] == "Australia/Sydney"


class TestCanHandle:
    """Tests for can_handle method."""

    def test_handles_time_keywords(self):
        expert = TimeExpert()
        assert expert.can_handle("What time is it?") is True
        assert expert.can_handle("Convert timezone") is True
        assert expert.can_handle("What's the UTC time?") is True

    def test_rejects_non_time_queries(self):
        expert = TimeExpert()
        assert expert.can_handle("Tell me a joke") is False
        assert expert.can_handle("What's the weather?") is False


class TestResolveTimezone:
    """Tests for _resolve_timezone method."""

    def test_resolve_alias(self):
        expert = TimeExpert()
        tz = expert._resolve_timezone("tokyo")
        assert tz == "Asia/Tokyo"

    def test_resolve_iana(self):
        expert = TimeExpert()
        tz = expert._resolve_timezone("America/New_York")
        assert tz == "America/New_York"

    def test_resolve_utc(self):
        expert = TimeExpert()
        tz = expert._resolve_timezone("UTC")
        assert tz == "UTC"

    def test_resolve_unknown_returns_original(self):
        expert = TimeExpert()
        tz = expert._resolve_timezone("unknown_tz")
        assert tz == "unknown_tz"

    def test_resolve_empty_returns_utc(self):
        expert = TimeExpert()
        tz = expert._resolve_timezone("")
        assert tz == "UTC"


class TestGetCotExamples:
    """Tests for CoT examples loading."""

    def test_loads_examples(self):
        expert = TimeExpert()
        examples = expert.get_cot_examples()

        assert examples.expert_name == "time"
        assert len(examples.examples) > 0

    def test_examples_have_queries(self):
        expert = TimeExpert()
        examples = expert.get_cot_examples()

        for ex in examples.examples:
            assert ex.query is not None
            assert len(ex.query) > 0

    def test_examples_have_actions(self):
        expert = TimeExpert()
        examples = expert.get_cot_examples()

        for ex in examples.examples:
            assert ex.action is not None
            assert ex.action.expert in ["time", "none"]


class TestGetCalibrationData:
    """Tests for calibration data."""

    def test_returns_tuple(self):
        expert = TimeExpert()
        result = expert.get_calibration_data()

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_positive_actions_target_time(self):
        expert = TimeExpert()
        positive, _ = expert.get_calibration_data()

        import json

        for action_json in positive:
            action = json.loads(action_json)
            assert action["expert"] == "time"

    def test_no_negative_actions_in_expert(self):
        expert = TimeExpert()
        _, negative = expert.get_calibration_data()
        assert negative == []


# Integration tests that require MCP server
@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests that call the actual MCP server."""

    def test_execute_get_time(self):
        expert = TimeExpert()
        result = expert.execute_operation("get_time", {"timezone": "UTC"})

        assert result["query_type"] == TimeQueryType.CURRENT_TIME.value
        assert result["timezone"] == "UTC"
        assert "iso8601" in result

    def test_execute_get_time_with_alias(self):
        expert = TimeExpert()
        result = expert.execute_operation("get_time", {"timezone": "tokyo"})

        assert result["timezone"] == "Asia/Tokyo"
        assert result["abbreviation"] == "JST"

    def test_execute_convert_time(self):
        expert = TimeExpert()
        result = expert.execute_operation(
            "convert_time",
            {
                "time": "2024-01-15T09:00:00",
                "from_timezone": "America/New_York",
                "to_timezone": "Asia/Tokyo",
            },
        )

        assert result["query_type"] == TimeQueryType.CONVERSION.value
        assert result["from_timezone"] == "America/New_York"
        assert result["to_timezone"] == "Asia/Tokyo"

    def test_execute_get_timezone_info(self):
        expert = TimeExpert()
        result = expert.execute_operation("get_timezone_info", {"location": "tokyo"})

        assert result["query_type"] == TimeQueryType.TIMEZONE_INFO.value
        assert result["iana_timezone"] == "Asia/Tokyo"

    def test_execute_action(self):
        expert = TimeExpert()
        action = VirtualExpertAction(
            expert="time",
            operation="get_time",
            parameters={"timezone": "UTC"},
        )
        result = expert.execute(action)

        assert isinstance(result, VirtualExpertResult)
        assert result.success is True
        assert result.data is not None
        assert result.expert_name == "time"

    def test_execute_failure(self):
        expert = TimeExpert()
        action = VirtualExpertAction(
            expert="time",
            operation="invalid_op",
        )
        result = expert.execute(action)

        assert result.success is False
        assert result.error is not None
