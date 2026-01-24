"""
Trace generator for time virtual expert training examples.

Generates trace examples demonstrating time operations (get_time,
convert_time, get_timezone_info) for CoT training data.
"""

from __future__ import annotations

import random
from typing import Any

from chuk_virtual_expert_time.expert import TIMEZONE_ALIASES

# Common IANA timezones for generation
IANA_TIMEZONES = [
    "UTC",
    "America/New_York",
    "America/Los_Angeles",
    "America/Chicago",
    "America/Denver",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Europe/Moscow",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Asia/Dubai",
    "Asia/Kolkata",
    "Australia/Sydney",
]

# Sample datetime strings for convert_time examples
SAMPLE_DATETIMES = [
    "2024-01-15T09:00:00",
    "2024-03-20T14:30:00",
    "2024-06-01T08:00:00",
    "2024-07-04T12:00:00",
    "2024-09-15T18:45:00",
    "2024-11-28T10:00:00",
    "2024-12-25T00:00:00",
    "2025-01-01T00:00:00",
]

# Query templates for natural language prompts
GET_TIME_QUERIES = [
    "What time is it in {city}?",
    "What's the current time in {tz}?",
    "Tell me the time in {city}",
    "Current time for {tz}?",
    "What time is it now in {city}?",
]

CONVERT_TIME_QUERIES = [
    "Convert {time} from {from_tz} to {to_tz}",
    "What is {time} {from_tz} in {to_tz}?",
    "If it's {time} in {from_tz}, what time is it in {to_tz}?",
    "Convert the time {time} from {from_tz} to {to_tz}",
]

TIMEZONE_INFO_QUERIES = [
    "What timezone is {city} in?",
    "Timezone info for {tz}",
    "Tell me about the {city} timezone",
    "What's the UTC offset for {tz}?",
]

# City names mapped to IANA timezones
CITY_TO_TZ: dict[str, str] = {
    "Tokyo": "Asia/Tokyo",
    "London": "Europe/London",
    "New York": "America/New_York",
    "Los Angeles": "America/Los_Angeles",
    "Paris": "Europe/Paris",
    "Sydney": "Australia/Sydney",
    "Berlin": "Europe/Berlin",
    "Moscow": "Europe/Moscow",
    "Beijing": "Asia/Shanghai",
    "Singapore": "Asia/Singapore",
    "Dubai": "Asia/Dubai",
    "Mumbai": "Asia/Kolkata",
    "Chicago": "America/Chicago",
    "Denver": "America/Denver",
}


class TimeTraceGenerator:
    """
    Generates time trace examples for training data.

    Produces examples with natural language queries and corresponding
    trace steps that demonstrate time expert operations.

    Args:
        seed: Random seed for reproducibility
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def generate_get_time(self, n: int = 10) -> list[dict[str, Any]]:
        """Generate get_time trace examples."""
        examples: list[dict[str, Any]] = []
        cities = list(CITY_TO_TZ.keys())

        for _ in range(n):
            city = self._rng.choice(cities)
            tz = CITY_TO_TZ[city]
            query_template = self._rng.choice(GET_TIME_QUERIES)
            query = query_template.format(city=city, tz=tz)

            trace = [
                {"get_time": {"timezone": tz, "var": "result"}},
                {"query": "result"},
            ]

            examples.append(
                {
                    "expert": "time",
                    "operation": "execute_trace",
                    "question": query,
                    "trace": trace,
                    "timezone": tz,
                }
            )

        return examples

    def generate_convert_time(self, n: int = 10) -> list[dict[str, Any]]:
        """Generate convert_time trace examples."""
        examples: list[dict[str, Any]] = []
        cities = list(CITY_TO_TZ.keys())

        for _ in range(n):
            from_city = self._rng.choice(cities)
            to_city = self._rng.choice([c for c in cities if c != from_city])
            from_tz = CITY_TO_TZ[from_city]
            to_tz = CITY_TO_TZ[to_city]
            dt = self._rng.choice(SAMPLE_DATETIMES)

            query_template = self._rng.choice(CONVERT_TIME_QUERIES)
            query = query_template.format(time=dt, from_tz=from_city, to_tz=to_city)

            trace = [
                {
                    "convert_time": {
                        "time": dt,
                        "from_timezone": from_tz,
                        "to_timezone": to_tz,
                        "var": "result",
                    }
                },
                {"query": "result"},
            ]

            examples.append(
                {
                    "expert": "time",
                    "operation": "execute_trace",
                    "question": query,
                    "trace": trace,
                    "from_timezone": from_tz,
                    "to_timezone": to_tz,
                    "datetime": dt,
                }
            )

        return examples

    def generate_timezone_info(self, n: int = 10) -> list[dict[str, Any]]:
        """Generate get_timezone_info trace examples."""
        examples: list[dict[str, Any]] = []
        cities = list(CITY_TO_TZ.keys())

        for _ in range(n):
            city = self._rng.choice(cities)
            tz = CITY_TO_TZ[city]
            query_template = self._rng.choice(TIMEZONE_INFO_QUERIES)
            query = query_template.format(city=city, tz=tz)

            trace = [
                {"get_timezone_info": {"location": tz, "var": "result"}},
                {"query": "result"},
            ]

            examples.append(
                {
                    "expert": "time",
                    "operation": "execute_trace",
                    "question": query,
                    "trace": trace,
                    "timezone": tz,
                }
            )

        return examples

    def generate_multi_step(self, n: int = 5) -> list[dict[str, Any]]:
        """Generate multi-step trace examples (e.g., get time then convert)."""
        examples: list[dict[str, Any]] = []
        cities = list(CITY_TO_TZ.keys())

        for _ in range(n):
            city1 = self._rng.choice(cities)
            city2 = self._rng.choice([c for c in cities if c != city1])
            tz1 = CITY_TO_TZ[city1]
            tz2 = CITY_TO_TZ[city2]

            query = f"Get the current time in {city1} and tell me what time that is in {city2}"

            trace = [
                {"get_time": {"timezone": tz1, "var": "current_time"}},
                {
                    "convert_time": {
                        "time_var": "current_time",
                        "from_timezone": tz1,
                        "to_timezone": tz2,
                        "var": "converted",
                    }
                },
                {"query": "converted"},
            ]

            examples.append(
                {
                    "expert": "time",
                    "operation": "execute_trace",
                    "question": query,
                    "trace": trace,
                    "from_timezone": tz1,
                    "to_timezone": tz2,
                }
            )

        return examples

    def generate_all(self, n_per_type: int = 5) -> list[dict[str, Any]]:
        """Generate examples of all types."""
        examples: list[dict[str, Any]] = []
        examples.extend(self.generate_get_time(n_per_type))
        examples.extend(self.generate_convert_time(n_per_type))
        examples.extend(self.generate_timezone_info(n_per_type))
        examples.extend(self.generate_multi_step(n_per_type))
        self._rng.shuffle(examples)
        return examples

    def get_timezone_aliases(self) -> dict[str, str]:
        """Return timezone aliases for reference."""
        return dict(TIMEZONE_ALIASES)
