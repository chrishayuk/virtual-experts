"""
Time virtual expert backed by MCP server.

Pydantic-native, async-native, no magic strings.
Delegates to the hosted MCP time server at https://time.chukai.io/mcp
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Any, ClassVar

from chuk_virtual_expert.mcp_expert import MCPExpert
from chuk_virtual_expert.models import TraceResult
from chuk_virtual_expert.trace_models import (
    BaseTraceStep,
    ConvertTimeStep,
    GetTimeStep,
    GetTimezoneInfoStep,
    InitStep,
    QueryStep,
    TraceStep,
)
from pydantic import TypeAdapter

_step_adapter: TypeAdapter[TraceStep] = TypeAdapter(TraceStep)


class TimeOperation(str, Enum):
    """Operations supported by the time expert."""

    GET_TIME = "get_time"
    CONVERT_TIME = "convert_time"
    GET_TIMEZONE_INFO = "get_timezone_info"


class TimeMCPTool(str, Enum):
    """MCP tool names from chuk-mcp-time server."""

    GET_LOCAL_TIME = "get_local_time"
    CONVERT_TIME = "convert_time"
    GET_TIMEZONE_INFO = "get_timezone_info"
    LIST_TIMEZONES = "list_timezones"
    GET_TIME_UTC = "get_time_utc"
    COMPARE_SYSTEM_CLOCK = "compare_system_clock"


class TimeQueryType(str, Enum):
    """Query result types for time expert."""

    CURRENT_TIME = "current_time"
    CONVERSION = "conversion"
    TIMEZONE_INFO = "timezone_info"
    ERROR = "error"


class AccuracyMode(str, Enum):
    """Accuracy mode for MCP time queries."""

    FAST = "fast"
    ACCURATE = "accurate"


# Timezone aliases for common names (used for parameter normalization)
TIMEZONE_ALIASES: dict[str, str] = {
    # Cities
    "tokyo": "Asia/Tokyo",
    "london": "Europe/London",
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "la": "America/Los_Angeles",
    "los angeles": "America/Los_Angeles",
    "paris": "Europe/Paris",
    "sydney": "Australia/Sydney",
    "berlin": "Europe/Berlin",
    "moscow": "Europe/Moscow",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "singapore": "Asia/Singapore",
    "dubai": "Asia/Dubai",
    "mumbai": "Asia/Kolkata",
    # Abbreviations
    "est": "America/New_York",
    "pst": "America/Los_Angeles",
    "cst": "America/Chicago",
    "mst": "America/Denver",
    "gmt": "Europe/London",
    "cet": "Europe/Paris",
    "jst": "Asia/Tokyo",
    "utc": "UTC",
}


class TimeExpert(MCPExpert):
    """
    Virtual expert for time and timezone operations.

    Delegates to the hosted MCP time server for NTP-accurate time.

    Operations:
        - get_time: Get current time in a timezone
        - convert_time: Convert time between timezones
        - get_timezone_info: Get timezone information for a location
    """

    # Class configuration
    name: ClassVar[str] = "time"
    description: ClassVar[str] = "Get current time and perform timezone conversions"
    version: ClassVar[str] = "3.0.0"
    priority: ClassVar[int] = 5

    # MCP server configuration
    mcp_server_url: ClassVar[str] = "https://time.chukai.io/mcp"
    mcp_timeout: ClassVar[float] = 30.0

    # File paths for CoT examples and schema (in data/ subdirectory)
    cot_examples_file: ClassVar[str] = "data/cot_examples.json"
    schema_file: ClassVar[str] = "data/schema.json"
    calibration_file: ClassVar[str] = "data/calibration.json"

    # Keywords for can_handle check
    _TIME_KEYWORDS: ClassVar[list[str]] = [
        "time",
        "timezone",
        "clock",
        "utc",
        "gmt",
        "est",
        "pst",
        "cst",
        "jst",
        "convert",
    ]

    def can_handle(self, prompt: str) -> bool:
        """
        Check if this expert can handle the given prompt.

        Uses time-related keywords for fast pre-filtering.
        """
        prompt_lower = prompt.lower()
        return any(kw in prompt_lower for kw in self._TIME_KEYWORDS)

    def get_operations(self) -> list[str]:
        """Return list of available operations."""
        return [op.value for op in TimeOperation] + ["execute_trace"]

    def get_mcp_tool_name(self, operation: str) -> str:
        """Map virtual expert operation to MCP tool name."""
        op = TimeOperation(operation)

        mapping = {
            TimeOperation.GET_TIME: TimeMCPTool.GET_LOCAL_TIME,
            TimeOperation.CONVERT_TIME: TimeMCPTool.CONVERT_TIME,
            TimeOperation.GET_TIMEZONE_INFO: TimeMCPTool.GET_TIMEZONE_INFO,
        }

        tool = mapping.get(op)
        if not tool:
            raise ValueError(f"Unknown operation: {operation}")

        return tool.value

    def transform_parameters(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Transform virtual expert parameters to MCP tool arguments."""
        op = TimeOperation(operation)

        if op == TimeOperation.GET_TIME:
            # Resolve timezone alias and map parameter name
            timezone = parameters.get("timezone", "UTC")
            resolved = self._resolve_timezone(timezone)
            return {"timezone": resolved, "mode": AccuracyMode.FAST.value}

        elif op == TimeOperation.CONVERT_TIME:
            # Map parameter names and resolve timezones
            return {
                "datetime_str": parameters.get("time", ""),
                "from_timezone": self._resolve_timezone(parameters.get("from_timezone", "UTC")),
                "to_timezone": self._resolve_timezone(parameters.get("to_timezone", "UTC")),
            }

        elif op == TimeOperation.GET_TIMEZONE_INFO:
            # Resolve location to timezone
            location = parameters.get("location", "")
            resolved = self._resolve_timezone(location)
            return {"timezone": resolved, "mode": AccuracyMode.FAST.value}

        return parameters

    def transform_result(self, operation: str, tool_result: dict[str, Any]) -> dict[str, Any]:
        """Transform MCP tool result to virtual expert format."""
        op = TimeOperation(operation)

        # Handle error results
        if "error" in tool_result:
            return {
                "query_type": TimeQueryType.ERROR.value,
                "error": tool_result["error"],
            }

        if op == TimeOperation.GET_TIME:
            return self._transform_get_time_result(tool_result)
        elif op == TimeOperation.CONVERT_TIME:
            return self._transform_convert_time_result(tool_result)
        elif op == TimeOperation.GET_TIMEZONE_INFO:
            return self._transform_timezone_info_result(tool_result)

        return tool_result

    def _transform_get_time_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Transform get_local_time MCP result."""
        local_dt = result.get("local_datetime", "")
        utc_offset_secs = result.get("utc_offset_seconds", 0)
        # Convert seconds to +HH:MM format
        hours = abs(utc_offset_secs) // 3600
        mins = (abs(utc_offset_secs) % 3600) // 60
        sign = "+" if utc_offset_secs >= 0 else "-"
        utc_offset_str = f"{sign}{hours:02d}:{mins:02d}"

        return {
            "query_type": TimeQueryType.CURRENT_TIME.value,
            "timezone": result.get("timezone", ""),
            "iana_timezone": result.get("timezone", ""),
            "iso8601": local_dt,
            "formatted": local_dt,
            "epoch_ms": result.get("epoch_ms", 0),
            "utc_offset": utc_offset_str,
            "is_dst": result.get("is_dst", False),
            "abbreviation": result.get("abbreviation", ""),
            "source_utc": result.get("source_utc", ""),
            "estimated_error_ms": result.get("estimated_error_ms", 0),
        }

    def _transform_convert_time_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Transform convert_time MCP result."""
        return {
            "query_type": TimeQueryType.CONVERSION.value,
            "from_timezone": result.get("from_timezone", ""),
            "to_timezone": result.get("to_timezone", ""),
            "from_time": result.get("from_datetime", ""),
            "to_time": result.get("to_datetime", ""),
            "from_iso8601": result.get("from_datetime", ""),
            "to_iso8601": result.get("to_datetime", ""),
            "explanation": result.get("explanation", ""),
        }

    def _transform_timezone_info_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Transform get_timezone_info MCP result."""
        utc_offset_secs = result.get("current_offset_seconds", 0)
        # Convert seconds to +HH:MM format
        hours = abs(utc_offset_secs) // 3600
        mins = (abs(utc_offset_secs) % 3600) // 60
        sign = "+" if utc_offset_secs >= 0 else "-"
        utc_offset_str = f"{sign}{hours:02d}:{mins:02d}"

        return {
            "query_type": TimeQueryType.TIMEZONE_INFO.value,
            "location": result.get("timezone", ""),
            "iana_timezone": result.get("timezone", ""),
            "utc_offset": utc_offset_str,
            "is_dst": result.get("current_is_dst", False),
            "abbreviation": result.get("current_abbreviation", ""),
            "transitions": result.get("transitions", []),
        }

    async def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an operation, intercepting execute_trace locally."""
        if operation == "execute_trace":
            raw_steps = parameters.get("trace", [])
            try:
                steps = [_step_adapter.validate_python(s) for s in raw_steps]
            except Exception as e:
                return {
                    "success": False,
                    "answer": None,
                    "state": {},
                    "error": str(e),
                    "steps_executed": 0,
                    "formatted": "",
                }
            result = await self._execute_trace(steps)
            return {
                "success": result.success,
                "answer": result.answer,
                "state": result.state,
                "error": result.error,
                "steps_executed": result.steps_executed,
                "formatted": str(result.answer) if result.answer is not None else "",
            }
        return await super().execute_operation(operation, parameters)

    async def _execute_trace(self, steps: Sequence[BaseTraceStep]) -> TraceResult:
        """
        Execute a sequence of typed time trace steps.

        Uses isinstance dispatch on typed step models.
        """
        state: dict[str, Any] = {}
        query_var: str | None = None
        steps_executed = 0

        for i, step in enumerate(steps):
            try:
                if isinstance(step, InitStep):
                    state[step.var] = step.value

                elif isinstance(step, GetTimeStep):
                    result = await super().execute_operation(
                        TimeOperation.GET_TIME.value,
                        {"timezone": step.timezone},
                    )
                    state[step.var] = result

                elif isinstance(step, ConvertTimeStep):
                    # Support referencing a time_var from state
                    time_str = step.time
                    if step.time_var and step.time_var in state:
                        stored = state[step.time_var]
                        if isinstance(stored, dict):
                            time_str = str(stored.get("iso8601", stored.get("formatted", "")))
                        else:
                            time_str = str(stored)
                    result = await super().execute_operation(
                        TimeOperation.CONVERT_TIME.value,
                        {
                            "time": time_str,
                            "from_timezone": step.from_timezone,
                            "to_timezone": step.to_timezone,
                        },
                    )
                    state[step.var] = result

                elif isinstance(step, GetTimezoneInfoStep):
                    result = await super().execute_operation(
                        TimeOperation.GET_TIMEZONE_INFO.value,
                        {"location": step.location},
                    )
                    state[step.var] = result

                elif isinstance(step, QueryStep):
                    query_var = step.var

                else:
                    return TraceResult(
                        success=False,
                        error=f"Step {i}: Unknown time step type: {type(step).__name__}",
                        state=state,
                        expert=self.name,
                        steps_executed=steps_executed,
                    )

                steps_executed += 1

            except Exception as e:
                return TraceResult(
                    success=False,
                    error=f"Step {i}: {e}",
                    state=state,
                    expert=self.name,
                    steps_executed=steps_executed,
                )

        # Resolve answer
        answer = state.get(query_var) if query_var else None

        return TraceResult(
            success=True,
            answer=answer,
            state=state,
            expert=self.name,
            steps_executed=steps_executed,
        )

    def _resolve_timezone(self, name: str) -> str:
        """Resolve a timezone name or alias to IANA format."""
        if not name:
            return "UTC"

        original = name.strip()
        lookup_name = original.lower()

        # Check aliases first
        if lookup_name in TIMEZONE_ALIASES:
            return TIMEZONE_ALIASES[lookup_name]

        # If it looks like an IANA timezone or is UTC, use as-is
        if "/" in original or lookup_name == "utc":
            return original

        # Return as-is and let MCP server handle it
        return original
