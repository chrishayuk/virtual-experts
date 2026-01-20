"""
Lazarus adapter for new VirtualExpert classes.

Bridges the clean Pydantic-based VirtualExpert API to Lazarus's
expected VirtualExpertPlugin interface.
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

    Lazarus expects:
    - name, description, priority attributes
    - can_handle(prompt) -> bool
    - execute(prompt) -> str
    - get_calibration_prompts() -> tuple[list[str], list[str]]

    This adapter provides those interfaces using the new clean API.

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
        """
        Check if expert can handle this prompt.

        Uses domain-specific keywords, not generic words.
        """
        # Domain-specific keywords for this expert
        keywords = self._get_domain_keywords()
        prompt_lower = prompt.lower()
        return any(kw in prompt_lower for kw in keywords)

    def _get_domain_keywords(self) -> list[str]:
        """Get domain-specific keywords for this expert."""
        if self._expert.name == "time":
            return [
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
        # Default: extract from operations
        return self._expert.get_operations()

    def execute(self, prompt: str) -> str | None:
        """
        Execute and return formatted string for Lazarus.

        Lazarus expects a string response, so we format the
        structured data appropriately.
        """
        from chuk_virtual_expert.models import VirtualExpertAction

        # Create a simple action from the prompt
        # In production, this would come from CoT extraction
        action = VirtualExpertAction(
            expert=self._expert.name,
            operation=self._get_default_operation(),
            parameters={"query": prompt},
            reasoning="Executed via Lazarus adapter",
        )

        # Try to parse timezone from prompt for time expert
        if self._expert.name == "time":
            action = self._parse_time_action(prompt)

        result = self._expert.execute(action)

        if result.success and result.data:
            return self._format_result(result.data)
        elif result.error:
            return f"Error: {result.error}"
        return None

    def _get_default_operation(self) -> str:
        """Get the default operation for this expert."""
        ops = self._expert.get_operations()
        return ops[0] if ops else "execute"

    def _parse_time_action(self, prompt: str) -> VirtualExpertAction:
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
        location_match = re.search(r"time\s+(?:in|at|for)\s+(\w+(?:\s+\w+)?)", prompt_lower)
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
        # Handle enum values
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

    def get_calibration_prompts(self) -> tuple[list[str], list[str]]:
        """
        Get calibration prompts for Lazarus router training (legacy).

        Returns the normalized action strings (not raw queries)
        for calibration. This ensures the router learns on
        the consistent action format.
        """
        positive, negative = self._expert.get_calibration_data()
        return positive, negative

    def get_calibration_actions(self) -> tuple[list[str], list[str]]:
        """
        Get calibration action JSONs for CoT-based router training.

        This is the preferred interface when CoT rewriting is enabled.
        Returns action JSONs that the router calibrates on.
        """
        return self._expert.get_calibration_data()

    def execute_action(self, action: Any) -> str | None:
        """
        Execute with a VirtualExpertAction (CoT interface).

        This method is called by Lazarus when CoT rewriting is enabled.
        Accepts either a Lazarus VirtualExpertAction (dataclass) or
        our Pydantic VirtualExpertAction.

        Args:
            action: VirtualExpertAction from Lazarus CoT rewriter

        Returns:
            Formatted string result for Lazarus
        """
        from chuk_virtual_expert.models import VirtualExpertAction as PydanticAction

        # Convert from Lazarus dataclass to our Pydantic model if needed
        if hasattr(action, "to_json"):
            # It's a Lazarus action dataclass - convert via JSON
            action_data = {
                "expert": action.expert,
                "operation": action.operation,
                "parameters": action.parameters,
                "confidence": action.confidence,
                "reasoning": action.reasoning,
            }
            pydantic_action = PydanticAction(**action_data)
        elif isinstance(action, PydanticAction):
            pydantic_action = action
        else:
            # Try to create from dict-like object
            pydantic_action = PydanticAction(
                expert=getattr(action, "expert", self._expert.name),
                operation=getattr(action, "operation", "execute"),
                parameters=getattr(action, "parameters", {}),
            )

        result = self._expert.execute(pydantic_action)

        if result.success and result.data:
            return self._format_result(result.data)
        elif result.error:
            return f"Error: {result.error}"
        return None

    def get_cot_examples(self) -> list[dict]:
        """
        Get CoT examples for few-shot prompting.

        Used by FewShotCoTRewriter to build the prompt.
        """
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
