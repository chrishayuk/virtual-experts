"""Tests for TimeExpert class."""

from datetime import datetime

import pytest
from chuk_virtual_expert.models import VirtualExpertAction, VirtualExpertResult

from chuk_virtual_expert_time.expert import (
    TIMEZONE_ALIASES,
    TimeExpert,
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
        assert expert.use_mcp is False
        assert expert.mcp_server == "chuk-mcp-time"

    def test_with_mcp_enabled(self):
        expert = TimeExpert(use_mcp=True)
        assert expert.use_mcp is True


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
        assert expert.version == "2.0.0"

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


class TestGetTime:
    """Tests for get_time operation."""

    def test_get_utc_time(self):
        expert = TimeExpert()
        result = expert.get_time("UTC")

        assert result["query_type"] == TimeQueryType.CURRENT_TIME
        assert result["timezone"] == "UTC"
        assert "iso8601" in result
        assert "formatted" in result
        assert "epoch_ms" in result

    def test_get_utc_time_default(self):
        expert = TimeExpert()
        result = expert.get_time()

        assert result["timezone"] == "UTC"

    def test_get_time_tokyo(self):
        expert = TimeExpert()
        result = expert.get_time("Asia/Tokyo")

        assert result["query_type"] == TimeQueryType.CURRENT_TIME
        assert result["timezone"] == "Asia/Tokyo"
        assert "utc_offset" in result

    def test_get_time_with_alias(self):
        expert = TimeExpert()
        result = expert.get_time("tokyo")

        assert result["timezone"] == "Asia/Tokyo"

    def test_get_time_epoch_ms_is_int(self):
        expert = TimeExpert()
        result = expert.get_time()

        assert isinstance(result["epoch_ms"], int)

    def test_get_time_iso8601_format(self):
        expert = TimeExpert()
        result = expert.get_time()

        iso_str = result["iso8601"]
        # Should be parseable as ISO8601
        datetime.fromisoformat(iso_str)


class TestConvertTime:
    """Tests for convert_time operation."""

    def test_convert_basic(self):
        expert = TimeExpert()
        result = expert.convert_time(
            time="3pm",
            from_timezone="America/New_York",
            to_timezone="America/Los_Angeles",
        )

        assert result["query_type"] == TimeQueryType.CONVERSION
        assert result["from_timezone"] == "America/New_York"
        assert result["to_timezone"] == "America/Los_Angeles"
        assert "from_time" in result
        assert "to_time" in result

    def test_convert_with_aliases(self):
        expert = TimeExpert()
        result = expert.convert_time(
            time="12pm",
            from_timezone="est",
            to_timezone="pst",
        )

        assert result["from_timezone"] == "America/New_York"
        assert result["to_timezone"] == "America/Los_Angeles"

    def test_convert_includes_iso8601(self):
        expert = TimeExpert()
        result = expert.convert_time(
            time="15:00",
            from_timezone="UTC",
            to_timezone="Asia/Tokyo",
        )

        assert "from_iso8601" in result
        assert "to_iso8601" in result


class TestGetTimezoneInfo:
    """Tests for get_timezone_info operation."""

    def test_known_location(self):
        expert = TimeExpert()
        result = expert.get_timezone_info("sydney")

        assert result["query_type"] == TimeQueryType.TIMEZONE_INFO
        assert result["location"] == "Sydney"
        assert result["iana_timezone"] == "Australia/Sydney"

    def test_unknown_location(self):
        expert = TimeExpert()
        result = expert.get_timezone_info("narnia")

        assert result["query_type"] == TimeQueryType.ERROR
        assert "error" in result


class TestExecuteOperation:
    """Tests for execute_operation dispatch method."""

    def test_dispatch_get_time(self):
        expert = TimeExpert()
        result = expert.execute_operation("get_time", {"timezone": "UTC"})

        assert result["query_type"] == TimeQueryType.CURRENT_TIME

    def test_dispatch_convert_time(self):
        expert = TimeExpert()
        result = expert.execute_operation(
            "convert_time",
            {
                "time": "3pm",
                "from_timezone": "EST",
                "to_timezone": "PST",
            },
        )

        assert result["query_type"] == TimeQueryType.CONVERSION

    def test_dispatch_get_timezone_info(self):
        expert = TimeExpert()
        result = expert.execute_operation(
            "get_timezone_info",
            {"location": "tokyo"},
        )

        assert result["query_type"] == TimeQueryType.TIMEZONE_INFO

    def test_dispatch_unknown_operation(self):
        expert = TimeExpert()

        with pytest.raises(ValueError):
            expert.execute_operation("unknown_op", {})


class TestExecute:
    """Tests for execute method (action interface)."""

    def test_execute_success(self):
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

    def test_resolve_unknown(self):
        expert = TimeExpert()
        tz = expert._resolve_timezone("unknown_tz")
        assert tz is None


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

    def test_negative_actions_dont_target_time(self):
        expert = TimeExpert()
        _, negative = expert.get_calibration_data()

        import json

        for action_json in negative:
            action = json.loads(action_json)
            assert action["expert"] != "time"
