"""Tests for TimeExpert trace execution and TimeTraceGenerator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from chuk_virtual_expert.trace_models import (
    ConvertTimeStep,
    GetTimeStep,
    GetTimezoneInfoStep,
    QueryStep,
)

from chuk_virtual_expert_time import TimeExpert, TimeTraceGenerator

# --- Trace Execution Tests ---


class TestTimeExpertTraceOperations:
    """Tests for execute_trace via execute_operation."""

    def setup_method(self) -> None:
        self.expert = TimeExpert()

    def test_get_operations_includes_execute_trace(self) -> None:
        ops = self.expert.get_operations()
        assert "execute_trace" in ops

    @pytest.mark.asyncio
    async def test_init_and_query_step(self) -> None:
        """Test basic init + query without MCP calls."""
        params = {
            "trace": [
                {"op": "init", "var": "tz", "value": "Asia/Tokyo"},
                {"op": "query", "var": "tz"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"] == "Asia/Tokyo"
        assert result["steps_executed"] == 2

    @pytest.mark.asyncio
    async def test_unknown_step_fails(self) -> None:
        """Test that unhandled step types produce errors."""
        params = {
            "trace": [
                {"op": "compute", "compute_op": "add", "args": [1, 2], "var": "r"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert not result["success"]
        assert "Unknown time step type" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_step_parse_error(self) -> None:
        """Test that invalid step ops produce parse errors."""
        params = {
            "trace": [
                {"op": "unknown_op_xyz"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert not result["success"]

    @pytest.mark.asyncio
    async def test_empty_trace(self) -> None:
        """Test that empty trace succeeds with no answer."""
        params = {"trace": []}
        result = await self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"] is None
        assert result["steps_executed"] == 0

    @pytest.mark.asyncio
    async def test_query_nonexistent_var(self) -> None:
        """Test querying a variable that doesn't exist."""
        params = {
            "trace": [
                {"op": "query", "var": "missing"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"] is None

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_get_time_step_calls_mcp(self, mock_exec: AsyncMock) -> None:
        """Test that get_time step delegates to MCP via parent."""
        mock_exec.return_value = {
            "query_type": "current_time",
            "timezone": "Asia/Tokyo",
            "iso8601": "2024-01-15T09:00:00+09:00",
            "formatted": "2024-01-15T09:00:00+09:00",
        }

        params = {
            "trace": [
                {"op": "get_time", "timezone": "Asia/Tokyo", "var": "tokyo_time"},
                {"op": "query", "var": "tokyo_time"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"]["timezone"] == "Asia/Tokyo"

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_convert_time_step_calls_mcp(self, mock_exec: AsyncMock) -> None:
        """Test that convert_time step delegates to MCP via parent."""
        mock_exec.return_value = {
            "query_type": "conversion",
            "from_timezone": "America/New_York",
            "to_timezone": "Asia/Tokyo",
            "from_time": "2024-01-15T09:00:00",
            "to_time": "2024-01-15T23:00:00",
        }

        params = {
            "trace": [
                {
                    "op": "convert_time",
                    "time": "2024-01-15T09:00:00",
                    "from_timezone": "America/New_York",
                    "to_timezone": "Asia/Tokyo",
                    "var": "converted",
                },
                {"op": "query", "var": "converted"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"]["to_timezone"] == "Asia/Tokyo"

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_get_timezone_info_step_calls_mcp(self, mock_exec: AsyncMock) -> None:
        """Test that get_timezone_info step delegates to MCP via parent."""
        mock_exec.return_value = {
            "query_type": "timezone_info",
            "iana_timezone": "Asia/Tokyo",
            "utc_offset": "+09:00",
            "is_dst": False,
        }

        params = {
            "trace": [
                {"op": "get_timezone_info", "location": "Asia/Tokyo", "var": "tz_info"},
                {"op": "query", "var": "tz_info"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"]["iana_timezone"] == "Asia/Tokyo"

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_convert_time_with_time_var_reference(self, mock_exec: AsyncMock) -> None:
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

        mock_exec.side_effect = [get_time_result, convert_result]

        params = {
            "trace": [
                {"op": "get_time", "timezone": "America/New_York", "var": "ny_time"},
                {
                    "op": "convert_time",
                    "time_var": "ny_time",
                    "from_timezone": "America/New_York",
                    "to_timezone": "Asia/Tokyo",
                    "var": "tokyo_time",
                },
                {"op": "query", "var": "tokyo_time"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert result["success"]
        assert result["answer"]["to_time"] == "2024-01-15T23:00:00+09:00"

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_mcp_error_in_trace(self, mock_exec: AsyncMock) -> None:
        """Test that MCP errors during trace are captured."""
        mock_exec.side_effect = ConnectionError("MCP server unavailable")

        params = {
            "trace": [
                {"op": "get_time", "timezone": "UTC", "var": "result"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert not result["success"]
        assert "MCP server unavailable" in result["error"]

    @pytest.mark.asyncio
    async def test_formatted_output(self) -> None:
        """Test that formatted field is populated correctly."""
        params = {
            "trace": [
                {"op": "init", "var": "x", "value": 42},
                {"op": "query", "var": "x"},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert result["formatted"] == "42"

    @pytest.mark.asyncio
    async def test_formatted_output_none(self) -> None:
        """Test formatted field when answer is None."""
        params = {
            "trace": [
                {"op": "init", "var": "x", "value": 42},
            ]
        }
        result = await self.expert.execute_operation("execute_trace", params)
        assert result["formatted"] == ""

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_non_trace_delegates_to_parent(self, mock_exec: AsyncMock) -> None:
        """Test that non-trace operations still delegate to parent."""
        mock_exec.return_value = {
            "query_type": "current_time",
            "timezone": "UTC",
            "iso8601": "2024-01-15T14:00:00Z",
        }

        result = await self.expert.execute_operation(
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
            assert ex.expert == "time"
            assert ex.expected_operation == "execute_trace"
            assert len(ex.trace) >= 2
            assert ex.query
            # Trace should have GetTimeStep and QueryStep
            assert isinstance(ex.trace[0], GetTimeStep)
            assert isinstance(ex.trace[-1], QueryStep)

    def test_generate_convert_time(self) -> None:
        examples = self.gen.generate_convert_time(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "time"
            assert ex.expected_params is not None
            assert "from_timezone" in ex.expected_params
            assert "to_timezone" in ex.expected_params
            assert "time" in ex.expected_params
            assert isinstance(ex.trace[0], ConvertTimeStep)

    def test_generate_timezone_info(self) -> None:
        examples = self.gen.generate_timezone_info(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "time"
            assert isinstance(ex.trace[0], GetTimezoneInfoStep)

    def test_generate_multi_step(self) -> None:
        examples = self.gen.generate_multi_step(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "time"
            assert ex.multi_step is True
            # Multi-step should have GetTimeStep then ConvertTimeStep
            assert isinstance(ex.trace[0], GetTimeStep)
            assert isinstance(ex.trace[1], ConvertTimeStep)
            assert isinstance(ex.trace[2], QueryStep)

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
        assert ex1 != ex2

    def test_get_timezone_aliases(self) -> None:
        aliases = self.gen.get_timezone_aliases()
        assert isinstance(aliases, dict)
        assert "tokyo" in aliases
        assert aliases["tokyo"] == "Asia/Tokyo"

    def test_queries_are_natural_language(self) -> None:
        examples = self.gen.generate_get_time(5)
        for ex in examples:
            assert len(ex.query) > 10

    def test_convert_time_from_to_different(self) -> None:
        """Ensure from and to timezones are always different."""
        examples = self.gen.generate_convert_time(20)
        for ex in examples:
            step = ex.trace[0]
            assert isinstance(step, ConvertTimeStep)
            assert step.from_timezone != step.to_timezone

    def test_model_dump_produces_valid_format(self) -> None:
        """Test that model_dump produces expected JSON structure."""
        examples = self.gen.generate_get_time(1)
        data = examples[0].model_dump()
        assert data["expert"] == "time"
        assert isinstance(data["trace"], list)
        assert data["trace"][0]["op"] == "get_time"
        assert data["trace"][1]["op"] == "query"
