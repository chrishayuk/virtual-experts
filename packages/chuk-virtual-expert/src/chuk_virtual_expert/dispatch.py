"""
Clean CoT-based dispatcher for virtual experts.

Uses Pydantic models and few-shot examples for reliable extraction.
"""

from __future__ import annotations

import json
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

# Import at runtime to avoid circular imports but still have type info
from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.models import (
    DispatchResult,
    VirtualExpertAction,
)
from chuk_virtual_expert.registry_v2 import ExpertRegistry


@runtime_checkable
class ActionExtractor(Protocol):
    """Protocol for extracting structured actions from queries."""

    def extract(
        self,
        query: str,
        available_experts: list[str],
    ) -> VirtualExpertAction:
        """Extract a structured action from a natural language query."""
        ...


class FewShotExtractor(BaseModel):
    """
    Extracts actions using few-shot prompting.

    Loads examples from each expert's cot_examples.json and includes
    them in the prompt for reliable extraction.
    """

    model_config = {"arbitrary_types_allowed": True}

    # Injected dependencies
    experts: dict[str, VirtualExpert] = {}

    # Configuration
    max_examples_per_expert: int = 3

    def get_prompt(self, query: str) -> str:
        """
        Generate the extraction prompt with few-shot examples.

        The prompt includes:
        1. System instructions
        2. Available experts and their operations
        3. Few-shot examples from each expert
        4. The user query
        """
        # Build expert descriptions
        expert_descriptions = []
        for name, expert in self.experts.items():
            schema = expert.get_schema()
            ops_summary = schema.get_operations_summary()
            expert_descriptions.append(f"**{name}**: {expert.description}\n{ops_summary}")

        # Collect few-shot examples from all experts
        all_examples = []
        for expert in self.experts.values():
            examples = expert.get_cot_examples()
            for ex in examples.examples[: self.max_examples_per_expert]:
                all_examples.append(ex.to_few_shot_format())

        prompt = f"""You extract structured actions from user queries.

## Available Experts

{chr(10).join(expert_descriptions)}

## Output Format

Respond with ONLY a JSON object:
{{"expert": "<name or none>", "operation": "<op>", "parameters": {{...}}, "confidence": <0-1>, "reasoning": "<brief>"}}

## Examples

{chr(10).join(all_examples)}

## Query

Query: "{query}"
Action:"""
        return prompt

    def parse_response(self, response: str) -> VirtualExpertAction:
        """Parse LLM response into VirtualExpertAction."""
        try:
            # Find the first complete JSON object
            start = response.find("{")
            if start == -1:
                return VirtualExpertAction.none_action("No JSON object found")

            # Count braces to find the end
            depth = 0
            end = start
            in_string = False
            escape_next = False

            for i, char in enumerate(response[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                if char == "\\":
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            json_str = response[start:end]
            data = json.loads(json_str)

            return VirtualExpertAction(**data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return VirtualExpertAction.none_action(f"Failed to parse: {e}")


class Dispatcher(BaseModel):
    """
    Dispatcher that routes queries to virtual experts.

    Uses CoT extraction to normalize queries into structured actions,
    then executes the appropriate expert.

    Example:
        dispatcher = Dispatcher(registry=registry)
        dispatcher.set_extractor(llm_extractor)

        result = dispatcher.dispatch("What time is it in Tokyo?")
        # result.action = VirtualExpertAction(expert="time", ...)
        # result.result = VirtualExpertResult(data={...})
    """

    model_config = {"arbitrary_types_allowed": True}

    # Registry of available experts
    registry: ExpertRegistry

    # Optional action extractor (LLM-based)
    extractor: ActionExtractor | None = None

    def set_extractor(self, extractor: ActionExtractor) -> None:
        """Set the action extractor (usually LLM-based)."""
        self.extractor = extractor

    def dispatch(self, query: str) -> DispatchResult:
        """
        Dispatch a query to the appropriate expert.

        Flow:
        1. Extract structured action from query via extractor
        2. Look up expert in registry
        3. Execute expert with action
        4. Return result

        Args:
            query: User's natural language query

        Returns:
            DispatchResult with action and expert result

        Raises:
            ValueError: If no extractor is set
        """
        if not self.extractor:
            raise ValueError(
                "No extractor set. Use set_extractor() to configure an LLM-based "
                "action extractor. CoT extraction is required - no fallback."
            )

        # Extract action via CoT
        action = self.extractor.extract(
            query,
            self.registry.expert_names,
        )

        # Dispatch to expert
        return self.dispatch_action(action)

    def dispatch_action(self, action: VirtualExpertAction) -> DispatchResult:
        """
        Dispatch a pre-extracted action directly.

        Useful when the action has already been extracted elsewhere
        (e.g., by an external CoT system).

        Args:
            action: Pre-extracted VirtualExpertAction

        Returns:
            DispatchResult with action and expert result
        """
        result = None
        if not action.is_passthrough():
            expert = self.registry.get(action.expert)
            if expert:
                result = expert.execute(action)

        return DispatchResult(action=action, result=result)


class CalibrationData(BaseModel):
    """
    Calibration data for router training.

    Contains normalized action strings (not raw queries) for training
    the calibration router.
    """

    expert_name: str
    positive_actions: list[str]  # Actions that SHOULD route here
    negative_actions: list[str]  # Actions that should NOT route here

    @classmethod
    def from_expert(cls, expert: VirtualExpert) -> CalibrationData:
        """Generate calibration data from an expert's CoT examples."""
        positive, negative = expert.get_calibration_data()
        return cls(
            expert_name=expert.name,
            positive_actions=positive,
            negative_actions=negative,
        )
