"""Tests for TimeExpert trace execution and TimeTraceGenerator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from chuk_virtual_expert_time import TimeExpert, TimeTraceGenerator

# --- Trace Execution Tests ---


class TestTimeExpertTraceOperations:
    """Tests for execute_trace via execute_operation."""

    def setup_method(self) -> None:
        self.expert = TimeExpert()

    def test_get_operations_includes_execute_trace(self) -> None:
        ops = self.expert.get_operations()
        assert "execute_trace" in ops

    def test_init_and_query_step(self) -> None:
        """Test basic init + query without MCP calls."""
        params = {
            "trace": [
                {"init": "tz", "value": "Asia/Tokyo"},
                {"query": "tz"},
            ]
        }
        result = self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"] == "Asia/Tokyo"
        assert result["steps_executed"] == 2

    def test_unknown_step_fails(self) -> None:
        """Test that unknown trace operations produce errors."""
        params = {
            "trace": [
                {"unknown_op": {"something": "bad"}},
            ]
        }
        result = self.expert.execute_operation("execute_trace", params)
        assert not result["success"]
        assert "Unknown time operation" in result["error"]

    def test_empty_trace(self) -> None:
        """Test that empty trace succeeds with no answer."""
        params = {"trace": []}
        result = self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"] is None
        assert result["steps_executed"] == 0

    def test_query_nonexistent_var(self) -> None:
        """Test querying a variable that doesn't exist."""
        params = {
            "trace": [
                {"query": "missing"},
            ]
        }
        result = self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"] is None

    @patch.object(TimeExpert, "execute_operation_async", wraps=None)
    def test_get_time_step_calls_mcp(self, mock_async: AsyncMock) -> None:
        """Test that get_time step delegates to MCP via parent."""
        mock_result = {
            "query_type": "current_time",
            "timezone": "Asia/Tokyo",
            "iso8601": "2024-01-15T09:00:00+09:00",
            "formatted": "2024-01-15T09:00:00+09:00",
        }

        # We need to patch the parent's execute_operation_async
        with patch(
            "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            params = {
                "trace": [
                    {"get_time": {"timezone": "Asia/Tokyo", "var": "tokyo_time"}},
                    {"query": "tokyo_time"},
                ]
            }
            result = self.expert.execute_operation("execute_trace", params)
            assert result["success"]
            assert result["answer"]["timezone"] == "Asia/Tokyo"

    def test_convert_time_step_calls_mcp(self) -> None:
        """Test that convert_time step delegates to MCP via parent."""
        mock_result = {
            "query_type": "conversion",
            "from_timezone": "America/New_York",
            "to_timezone": "Asia/Tokyo",
            "from_time": "2024-01-15T09:00:00",
            "to_time": "2024-01-15T23:00:00",
        }

        with patch(
            "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            params = {
                "trace": [
                    {
                        "convert_time": {
                            "time": "2024-01-15T09:00:00",
                            "from_timezone": "America/New_York",
                            "to_timezone": "Asia/Tokyo",
                            "var": "converted",
                        }
                    },
                    {"query": "converted"},
                ]
            }
            result = self.expert.execute_operation("execute_trace", params)
            assert result["success"]
            assert result["answer"]["to_timezone"] == "Asia/Tokyo"

    def test_get_timezone_info_step_calls_mcp(self) -> None:
        """Test that get_timezone_info step delegates to MCP via parent."""
        mock_result = {
            "query_type": "timezone_info",
            "iana_timezone": "Asia/Tokyo",
            "utc_offset": "+09:00",
            "is_dst": False,
        }

        with patch(
            "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            params = {
                "trace": [
                    {"get_timezone_info": {"location": "Asia/Tokyo", "var": "tz_info"}},
                    {"query": "tz_info"},
                ]
            }
            result = self.expert.execute_operation("execute_trace", params)
            assert result["success"]
            assert result["answer"]["iana_timezone"] == "Asia/Tokyo"

    def test_convert_time_with_time_var_reference(self) -> None:
        """Test convert_time using a time_var reference from state."""
        get_time_result = {
            "query_type": "current_time",
            "timezone": "America/New_York",
            "iso8601": "2024-01-15T09:00:00-05:00",
            "formatted": "2024-01-15T09:00:00-05:00",
        }
        convert_result = {
            "query_type": "conversion",
            "from_timezone": "America/New_York",
            "to_timezone": "Asia/Tokyo",
            "to_time": "2024-01-15T23:00:00+09:00",
        }

        call_count = [0]

        async def mock_execute(*args: object, **kwargs: object) -> dict:
            call_count[0] += 1
            if call_count[0] == 1:
                return get_time_result
            return convert_result

        with patch(
            "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
            new_callable=AsyncMock,
            side_effect=mock_execute,
        ):
            params = {
                "trace": [
                    {"get_time": {"timezone": "America/New_York", "var": "ny_time"}},
                    {
                        "convert_time": {
                            "time_var": "ny_time",
                            "from_timezone": "America/New_York",
                            "to_timezone": "Asia/Tokyo",
                            "var": "tokyo_time",
                        }
                    },
                    {"query": "tokyo_time"},
                ]
            }
            result = self.expert.execute_operation("execute_trace", params)
            assert result["success"]
            assert result["answer"]["to_time"] == "2024-01-15T23:00:00+09:00"

    def test_mcp_error_in_trace(self) -> None:
        """Test that MCP errors during trace are captured."""
        with patch(
            "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
            new_callable=AsyncMock,
            side_effect=ConnectionError("MCP server unavailable"),
        ):
            params = {
                "trace": [
                    {"get_time": {"timezone": "UTC", "var": "result"}},
                ]
            }
            result = self.expert.execute_operation("execute_trace", params)
            assert not result["success"]
            assert "MCP server unavailable" in result["error"]

    def test_formatted_output(self) -> None:
        """Test that formatted field is populated correctly."""
        params = {
            "trace": [
                {"init": "x", "value": 42},
                {"query": "x"},
            ]
        }
        result = self.expert.execute_operation("execute_trace", params)
        assert result["formatted"] == "42"

    def test_formatted_output_none(self) -> None:
        """Test formatted field when answer is None."""
        params = {
            "trace": [
                {"init": "x", "value": 42},
            ]
        }
        result = self.expert.execute_operation("execute_trace", params)
        assert result["formatted"] == ""


# --- Async Trace Tests ---


class TestTimeExpertTraceAsync:
    """Tests for async trace execution."""

    def setup_method(self) -> None:
        self.expert = TimeExpert()

    @pytest.mark.asyncio
    async def test_execute_operation_async_trace(self) -> None:
        """Test async execute_operation_async with execute_trace."""
        mock_result = {
            "query_type": "current_time",
            "timezone": "UTC",
            "iso8601": "2024-01-15T14:00:00Z",
        }

        with patch(
            "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await self.expert.execute_operation_async(
                "execute_trace",
                {
                    "trace": [
                        {"get_time": {"timezone": "UTC", "var": "utc_time"}},
                        {"query": "utc_time"},
                    ]
                },
            )
            assert result["success"]
            assert result["answer"]["timezone"] == "UTC"

    @pytest.mark.asyncio
    async def test_async_non_trace_delegates_to_parent(self) -> None:
        """Test that non-trace operations still delegate to parent."""
        mock_result = {
            "query_type": "current_time",
            "timezone": "UTC",
            "iso8601": "2024-01-15T14:00:00Z",
        }

        with patch(
            "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await self.expert.execute_operation_async(
                "get_time",
                {"timezone": "UTC"},
            )
            assert result["query_type"] == "current_time"


# --- TimeTraceGenerator Tests ---


class TestTimeTraceGenerator:
    """Tests for TimeTraceGenerator."""

    def setup_method(self) -> None:
        self.gen = TimeTraceGenerator(seed=42)

    def test_generate_get_time(self) -> None:
        examples = self.gen.generate_get_time(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "time"
            assert ex["operation"] == "execute_trace"
            assert "trace" in ex
            assert "query" in ex
            assert "timezone" in ex
            # Trace should have get_time and query steps
            assert any("get_time" in step for step in ex["trace"])
            assert any("query" in step for step in ex["trace"])

    def test_generate_convert_time(self) -> None:
        examples = self.gen.generate_convert_time(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "time"
            assert "from_timezone" in ex
            assert "to_timezone" in ex
            assert "datetime" in ex
            assert any("convert_time" in step for step in ex["trace"])

    def test_generate_timezone_info(self) -> None:
        examples = self.gen.generate_timezone_info(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "time"
            assert "timezone" in ex
            assert any("get_timezone_info" in step for step in ex["trace"])

    def test_generate_multi_step(self) -> None:
        examples = self.gen.generate_multi_step(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "time"
            assert "from_timezone" in ex
            assert "to_timezone" in ex
            # Multi-step should have both get_time and convert_time
            ops = [next(iter(step)) for step in ex["trace"]]
            assert "get_time" in ops
            assert "convert_time" in ops

    def test_generate_all(self) -> None:
        examples = self.gen.generate_all(n_per_type=3)
        # 3 get_time + 3 convert_time + 3 timezone_info + 3 multi_step = 12
        assert len(examples) == 12

    def test_reproducible_with_seed(self) -> None:
        gen1 = TimeTraceGenerator(seed=123)
        gen2 = TimeTraceGenerator(seed=123)
        ex1 = gen1.generate_get_time(3)
        ex2 = gen2.generate_get_time(3)
        assert ex1 == ex2

    def test_different_seeds_different_results(self) -> None:
        gen1 = TimeTraceGenerator(seed=1)
        gen2 = TimeTraceGenerator(seed=2)
        ex1 = gen1.generate_get_time(10)
        ex2 = gen2.generate_get_time(10)
        # Very unlikely all 10 would match with different seeds
        assert ex1 != ex2

    def test_get_timezone_aliases(self) -> None:
        aliases = self.gen.get_timezone_aliases()
        assert isinstance(aliases, dict)
        assert "tokyo" in aliases
        assert aliases["tokyo"] == "Asia/Tokyo"

    def test_queries_are_natural_language(self) -> None:
        examples = self.gen.generate_get_time(5)
        for ex in examples:
            # Query should contain a city or timezone name
            assert len(ex["query"]) > 10  # Not just a keyword

    def test_convert_time_from_to_different(self) -> None:
        """Ensure from and to timezones are always different."""
        examples = self.gen.generate_convert_time(20)
        for ex in examples:
            assert ex["from_timezone"] != ex["to_timezone"]
