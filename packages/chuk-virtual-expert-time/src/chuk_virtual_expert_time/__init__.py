"""
chuk-virtual-expert-time: Time virtual expert backed by MCP server.

Provides accurate time and timezone operations via hosted MCP server.

Features:
- Get current time in any IANA timezone (NTP-accurate)
- Convert times between timezones
- Get timezone information for locations

Usage:
    from chuk_virtual_expert_time import TimeExpert, TimeOperation
    from chuk_virtual_expert.models import VirtualExpertAction

    expert = TimeExpert()

    # Using VirtualExpertAction
    action = VirtualExpertAction(
        expert="time",
        operation=TimeOperation.GET_TIME.value,
        parameters={"timezone": "Asia/Tokyo"}
    )
    result = expert.execute(action)
    print(result.data)

    # Using execute_operation directly
    result = expert.execute_operation(
        TimeOperation.GET_TIME.value,
        {"timezone": "Asia/Tokyo"}
    )
    print(result)

Async usage:
    result = await expert.execute_operation_async(
        TimeOperation.GET_TIME.value,
        {"timezone": "Asia/Tokyo"}
    )
"""

from chuk_virtual_expert_time.expert import (
    TIMEZONE_ALIASES,
    AccuracyMode,
    TimeExpert,
    TimeMCPTool,
    TimeOperation,
    TimeQueryType,
)
from chuk_virtual_expert_time.generators import TimeTraceGenerator

__all__ = [
    "TimeExpert",
    "TimeOperation",
    "TimeMCPTool",
    "TimeQueryType",
    "AccuracyMode",
    "TIMEZONE_ALIASES",
    "TimeTraceGenerator",
]

__version__ = "3.0.0"
