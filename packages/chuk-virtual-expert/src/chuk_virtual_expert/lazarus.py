"""
Lazarus adapter for VirtualExpert classes.

Provides string-based execute interface for Lazarus integration.
VirtualExpert now natively supports can_handle() and get_calibration_prompts().
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from chuk_virtual_expert.expert import VirtualExpert
    from chuk_virtual_expert.models import VirtualExpertAction


class LazarusAdapter:
    """
    Adapts a VirtualExpert for use with Lazarus.

    Provides the string-based execute(prompt) -> str interface
    that Lazarus expects. VirtualExpert now natively provides:
    - can_handle(prompt) -> bool
    - get_calibration_prompts() -> tuple[list[str], list[str]]

    Example:
        from chuk_virtual_expert.lazarus import LazarusAdapter
        from chuk_virtual_expert_time import TimeExpert

        expert = TimeExpert()
        adapter = LazarusAdapter(expert)

        # Now use with Lazarus
        registry.register(adapter)
    """

    def __init__(self, expert: VirtualExpert):
        self._expert = expert

    @property
    def name(self) -> str:
        return self._expert.name

    @property
    def description(self) -> str:
        return self._expert.description

    @property
    def priority(self) -> int:
        return self._expert.priority

    def can_handle(self, prompt: str) -> bool:
        """Delegate to expert's can_handle method."""
        return self._expert.can_handle(prompt)

    def get_calibration_prompts(self) -> tuple[list[str], list[str]]:
        """Delegate to expert's get_calibration_prompts method."""
        return self._expert.get_calibration_prompts()

    def execute(self, prompt: str) -> str | None:
        """
        Execute and return formatted string for Lazarus.

        Parses prompt into a VirtualExpertAction and executes it,
        then formats the structured result as a string.
        """

        # Parse prompt into action
        action = self._parse_prompt(prompt)
        result = self._expert.execute(action)

        if result.success and result.data:
            return self._format_result(result.data)
        elif result.error:
            return f"Error: {result.error}"
        return None

    def _parse_prompt(self, prompt: str) -> VirtualExpertAction:
        """Parse a prompt into a VirtualExpertAction."""
        from chuk_virtual_expert.models import VirtualExpertAction

        # Expert-specific parsing
        if self._expert.name == "time":
            return self._parse_time_prompt(prompt)

        # Default: use first operation with prompt as parameter
        ops = self._expert.get_operations()
        return VirtualExpertAction(
            expert=self._expert.name,
            operation=ops[0] if ops else "execute",
            parameters={"query": prompt},
            reasoning="Parsed via LazarusAdapter",
        )

    def _parse_time_prompt(self, prompt: str) -> VirtualExpertAction:
        """Parse a time-related prompt into an action."""
        import re

        from chuk_virtual_expert.models import VirtualExpertAction

        prompt_lower = prompt.lower()

        # Check for timezone conversion
        convert_match = re.search(
            r"(\d+[:\d]*)\s*(am|pm)?\s*(\w+)\s+(?:to|in)\s+(\w+)", prompt_lower
        )
        if convert_match:
            return VirtualExpertAction(
                expert="time",
                operation="convert_time",
                parameters={
                    "time": f"{convert_match.group(1)}{convert_match.group(2) or ''}",
                    "from_timezone": convert_match.group(3),
                    "to_timezone": convert_match.group(4),
                },
            )

        # Check for timezone info
        if "timezone" in prompt_lower:
            tz_match = re.search(r"timezone\s+(?:for|of|in|is)\s+(\w+)", prompt_lower)
            if tz_match:
                return VirtualExpertAction(
                    expert="time",
                    operation="get_timezone_info",
                    parameters={"location": tz_match.group(1)},
                )

        # Check for time in location
        location_match = re.search(r"time.*?\b(?:in|at|for)\s+(\w+(?:\s+\w+)?)", prompt_lower)
        if location_match:
            return VirtualExpertAction(
                expert="time",
                operation="get_time",
                parameters={"timezone": location_match.group(1)},
            )

        # Default: get UTC time
        return VirtualExpertAction(
            expert="time",
            operation="get_time",
            parameters={},
        )

    def _format_result(self, data: dict[str, Any]) -> str:
        """Format structured data as a string for Lazarus."""
        from enum import Enum

        query_type = data.get("query_type", "")
        if isinstance(query_type, Enum):
            query_type = query_type.value
        query_type = str(query_type)

        if "current_time" in query_type:
            tz = data.get("timezone", "UTC")
            formatted = data.get("formatted", data.get("iso8601", ""))
            return f"{formatted} ({tz})"

        elif "conversion" in query_type:
            from_time = data.get("from_time", "")
            to_time = data.get("to_time", "")
            from_tz = data.get("from_timezone", "")
            to_tz = data.get("to_timezone", "")
            return f"{from_time} {from_tz} = {to_time} {to_tz}"

        elif "timezone_info" in query_type:
            location = data.get("location", "")
            tz = data.get("iana_timezone", "")
            return f"{location} is in timezone {tz}"

        elif "error" in query_type:
            return f"Error: {data.get('error', 'Unknown error')}"

        # Fallback: JSON
        return json.dumps(data, default=str)

    def execute_action(self, action: Any) -> str | None:
        """
        Execute with a VirtualExpertAction.

        Args:
            action: VirtualExpertAction (Pydantic or dataclass)

        Returns:
            Formatted string result
        """
        from chuk_virtual_expert.models import VirtualExpertAction as PydanticAction

        # Convert to Pydantic model if needed
        if isinstance(action, PydanticAction):
            pydantic_action = action
        elif hasattr(action, "expert"):
            pydantic_action = PydanticAction(
                expert=action.expert,
                operation=action.operation,
                parameters=getattr(action, "parameters", {}),
                confidence=getattr(action, "confidence", 1.0),
                reasoning=getattr(action, "reasoning", ""),
            )
        else:
            return None

        result = self._expert.execute(pydantic_action)

        if result.success and result.data:
            return self._format_result(result.data)
        elif result.error:
            return f"Error: {result.error}"
        return None

    def get_calibration_actions(self) -> tuple[list[str], list[str]]:
        """Get calibration action JSONs for CoT-based routing."""
        return self._expert.get_calibration_data()

    def get_cot_examples(self) -> list[dict]:
        """Get CoT examples for few-shot prompting."""
        examples = self._expert.get_cot_examples()
        return [{"query": ex.query, "action": ex.action.model_dump()} for ex in examples.examples]

    def __repr__(self) -> str:
        return f"LazarusAdapter({self._expert!r})"


def adapt_expert(expert: VirtualExpert) -> LazarusAdapter:
    """
    Adapt a VirtualExpert for use with Lazarus.

    Args:
        expert: The VirtualExpert instance to adapt

    Returns:
        LazarusAdapter wrapping the expert
    """
    return LazarusAdapter(expert)
