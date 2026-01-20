"""
chuk-virtual-expert-time: Time virtual expert.

Provides accurate time and timezone operations.

Features:
- Get current time in any IANA timezone
- Convert times between timezones
- Get timezone information for locations

Usage:
    from chuk_virtual_expert_time import TimeExpert

    expert = TimeExpert()
    result = expert.get_time(timezone="Asia/Tokyo")
    print(result)  # {"query_type": "current_time", "timezone": "Asia/Tokyo", ...}

Usage (with action):
    from chuk_virtual_expert.models import VirtualExpertAction

    action = VirtualExpertAction(
        expert="time",
        operation="get_time",
        parameters={"timezone": "Asia/Tokyo"}
    )
    result = expert.execute(action)
"""

from chuk_virtual_expert_time.expert import (
    TIMEZONE_ALIASES,
    TimeExpert,
    TimeOperation,
    TimeQueryType,
)

__all__ = [
    "TimeExpert",
    "TimeOperation",
    "TimeQueryType",
    "TIMEZONE_ALIASES",
]

__version__ = "2.0.0"
