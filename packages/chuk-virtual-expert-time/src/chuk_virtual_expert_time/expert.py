"""
Clean time virtual expert implementation.

Pydantic-native, no magic strings, uses enums and constants.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar

from chuk_virtual_expert.expert import VirtualExpert
from pydantic import Field


class TimeOperation(str, Enum):
    """Operations supported by the time expert."""

    GET_TIME = "get_time"
    CONVERT_TIME = "convert_time"
    GET_TIMEZONE_INFO = "get_timezone_info"


class TimeQueryType(str, Enum):
    """Query result types for time expert."""

    CURRENT_TIME = "current_time"
    CONVERSION = "conversion"
    TIMEZONE_INFO = "timezone_info"
    ERROR = "error"


# Timezone aliases for common names
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


class TimeExpert(VirtualExpert):
    """
    Virtual expert for time and timezone operations.

    Returns structured data for model chain-of-thought reasoning.

    Operations:
        - get_time: Get current time in a timezone
        - convert_time: Convert time between timezones
        - get_timezone_info: Get timezone information for a location
    """

    # Class configuration
    name: ClassVar[str] = "time"
    description: ClassVar[str] = "Get current time and perform timezone conversions"
    version: ClassVar[str] = "2.0.0"
    priority: ClassVar[int] = 5

    # File paths
    cot_examples_file: ClassVar[str] = "cot_examples.json"
    schema_file: ClassVar[str] = "schema.json"

    # Instance configuration
    use_mcp: bool = Field(default=False, description="Whether to use MCP server")
    mcp_server: str = Field(default="chuk-mcp-time", description="MCP server name")

    def get_operations(self) -> list[str]:
        """Return list of available operations."""
        return [op.value for op in TimeOperation]

    def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a time operation."""
        op = TimeOperation(operation)

        if op == TimeOperation.GET_TIME:
            return self.get_time(**parameters)
        elif op == TimeOperation.CONVERT_TIME:
            return self.convert_time(**parameters)
        elif op == TimeOperation.GET_TIMEZONE_INFO:
            return self.get_timezone_info(**parameters)
        else:
            return {
                "query_type": TimeQueryType.ERROR,
                "error": f"Unknown operation: {operation}",
            }

    def get_time(self, timezone: str = "UTC") -> dict[str, Any]:
        """
        Get current time in a timezone.

        Args:
            timezone: IANA timezone or alias (default: UTC)

        Returns:
            Structured time data
        """
        tz_name = self._resolve_timezone(timezone) or timezone

        if tz_name.upper() == "UTC":
            return self._get_utc_time()

        return self._get_time_for_timezone(tz_name)

    def convert_time(
        self,
        time: str,
        from_timezone: str,
        to_timezone: str,
    ) -> dict[str, Any]:
        """
        Convert time between timezones.

        Args:
            time: Time string (e.g., "3pm", "15:00")
            from_timezone: Source timezone
            to_timezone: Target timezone

        Returns:
            Structured conversion result
        """
        from_tz = self._resolve_timezone(from_timezone) or from_timezone
        to_tz = self._resolve_timezone(to_timezone) or to_timezone

        try:
            from zoneinfo import ZoneInfo

            from dateutil import parser

            parsed = parser.parse(time)
            from_dt = parsed.replace(tzinfo=ZoneInfo(from_tz))
            to_dt = from_dt.astimezone(ZoneInfo(to_tz))

            return {
                "query_type": TimeQueryType.CONVERSION,
                "from_timezone": from_tz,
                "to_timezone": to_tz,
                "from_time": from_dt.strftime("%I:%M %p"),
                "to_time": to_dt.strftime("%I:%M %p"),
                "from_iso8601": from_dt.isoformat(),
                "to_iso8601": to_dt.isoformat(),
            }
        except ImportError:
            return {
                "query_type": TimeQueryType.ERROR,
                "error": "python-dateutil required for conversion",
            }
        except Exception as e:
            return {
                "query_type": TimeQueryType.ERROR,
                "error": str(e),
            }

    def get_timezone_info(self, location: str) -> dict[str, Any]:
        """
        Get timezone information for a location.

        Args:
            location: Location name or timezone

        Returns:
            Timezone info
        """
        tz = self._resolve_timezone(location.lower())

        if tz:
            return {
                "query_type": TimeQueryType.TIMEZONE_INFO,
                "location": location.title(),
                "iana_timezone": tz,
            }

        return {
            "query_type": TimeQueryType.ERROR,
            "location": location,
            "error": "Unknown location",
        }

    def _resolve_timezone(self, name: str) -> str | None:
        """Resolve a timezone name or alias to IANA format."""
        original = name.strip()
        lookup_name = original.lower()
        if lookup_name in TIMEZONE_ALIASES:
            return TIMEZONE_ALIASES[lookup_name]
        if "/" in original or lookup_name == "utc":
            return original
        return None

    def _get_utc_time(self) -> dict[str, Any]:
        """Get current UTC time."""
        now = datetime.now(UTC)
        return {
            "query_type": TimeQueryType.CURRENT_TIME,
            "timezone": "UTC",
            "iana_timezone": "UTC",
            "iso8601": now.isoformat(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
            "epoch_ms": int(now.timestamp() * 1000),
        }

    def _get_time_for_timezone(self, tz_name: str) -> dict[str, Any]:
        """Get current time for a specific timezone."""
        try:
            from zoneinfo import ZoneInfo

            now = datetime.now(ZoneInfo(tz_name))
            return {
                "query_type": TimeQueryType.CURRENT_TIME,
                "timezone": tz_name,
                "iana_timezone": tz_name,
                "iso8601": now.isoformat(),
                "formatted": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "epoch_ms": int(now.timestamp() * 1000),
                "utc_offset": now.strftime("%z"),
            }
        except Exception as e:
            return {
                "query_type": TimeQueryType.ERROR,
                "timezone": tz_name,
                "error": str(e),
            }
