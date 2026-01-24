"""
Clean base class for virtual experts.

Pydantic-native, no magic strings, uses the models module.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel

from chuk_virtual_expert.models import (
    CoTExample,
    CoTExamples,
    ExpertSchema,
    OperationSchema,
    ParameterSchema,
    VirtualExpertAction,
    VirtualExpertResult,
)


class VirtualExpert(ABC, BaseModel):
    """
    Base class for virtual experts.

    Virtual experts are specialized plugins that handle domain-specific
    queries with high accuracy. They return structured data that models
    can use for chain-of-thought reasoning.

    Example:
        class TimeExpert(VirtualExpert):
            name: ClassVar[str] = "time"
            description: ClassVar[str] = "Time and timezone operations"

            def get_time(self, timezone: str = "UTC") -> dict[str, Any]:
                ...

            def get_operations(self) -> list[str]:
                return ["get_time", "convert_time"]
    """

    # Class-level configuration (override in subclasses)
    name: ClassVar[str] = "base"
    description: ClassVar[str] = "Base virtual expert"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 0

    # File paths relative to the expert's module
    cot_examples_file: ClassVar[str] = "cot_examples.json"
    schema_file: ClassVar[str] = "schema.json"
    calibration_file: ClassVar[str] = "calibration.json"

    # Pydantic config
    model_config = {"arbitrary_types_allowed": True}

    # Cached data
    _cot_examples: CoTExamples | None = None
    _schema: ExpertSchema | None = None

    @abstractmethod
    def can_handle(self, prompt: str) -> bool:
        """
        Check if this expert can handle the given prompt.

        This is used as a fast pre-filter before the router makes its decision.
        Return True if the prompt might be handled by this expert.

        Args:
            prompt: The user's input prompt

        Returns:
            True if this expert can potentially handle the prompt
        """
        ...

    @abstractmethod
    def get_operations(self) -> list[str]:
        """
        Return list of available operation names.

        These should correspond to methods on this class.
        """
        ...

    @abstractmethod
    async def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a named operation with parameters.

        Args:
            operation: Operation name (e.g., "get_time")
            parameters: Operation parameters

        Returns:
            Structured result data
        """
        ...

    async def execute(self, action: VirtualExpertAction) -> VirtualExpertResult:
        """
        Execute a VirtualExpertAction and return result.

        This is the main entry point used by the dispatcher.
        """
        try:
            data = await self.execute_operation(action.operation, action.parameters)
            return VirtualExpertResult(
                data=data,
                expert_name=self.name,
                success=True,
                action=action,
            )
        except Exception as e:
            return VirtualExpertResult(
                data=None,
                expert_name=self.name,
                success=False,
                error=str(e),
                action=action,
            )

    def get_cot_examples(self) -> CoTExamples:
        """
        Load CoT training examples from JSON file.

        Returns cached examples if already loaded.
        """
        if self._cot_examples is None:
            self._cot_examples = self._load_cot_examples()
        return self._cot_examples

    def get_schema(self) -> ExpertSchema:
        """
        Load operation schema from JSON file.

        Returns cached schema if already loaded.
        """
        if self._schema is None:
            self._schema = self._load_schema()
        return self._schema

    def get_calibration_data(self) -> tuple[list[str], list[str]]:
        """
        Get calibration data for router training (JSON actions).

        Returns actions formatted as JSON strings for calibration.
        The router learns to distinguish between actions that should
        route to this expert vs. other experts.

        Returns:
            Tuple of (positive_actions, negative_actions) as JSON strings
        """
        examples = self.get_cot_examples()
        return examples.positive_actions, examples.negative_actions

    def get_calibration_actions(self) -> tuple[list[str], list[str]]:
        """
        Get calibration actions for CoT-based router training.

        Alias for get_calibration_data() - returns JSON action strings.
        Used by Lazarus dense wrapper for CoT-based calibration.

        Returns:
            Tuple of (positive_actions, negative_actions) as JSON strings
        """
        return self.get_calibration_data()

    def get_calibration_prompts(self) -> tuple[list[str], list[str]]:
        """
        Get calibration prompts for router training (plain text).

        Returns plain text prompts for activation-space routing.
        Used by routers that learn to distinguish prompts in hidden state space.

        Returns:
            Tuple of (positive_prompts, negative_prompts) as plain text
        """
        # Try to load from calibration.json
        calibration_path = self._get_package_dir() / self.calibration_file
        if calibration_path.exists():
            with open(calibration_path) as f:
                data = json.load(f)
            return data.get("positive", []), data.get("negative", [])

        # Fallback: extract queries from cot_examples
        examples = self.get_cot_examples()
        positive = [ex.query for ex in examples.examples if ex.action.expert == self.name]
        negative = [ex.query for ex in examples.examples if ex.action.expert != self.name]
        return positive, negative

    def get_few_shot_prompt(self, max_examples: int = 5) -> str:
        """
        Get few-shot examples for CoT extraction prompt.

        Args:
            max_examples: Maximum number of examples to include

        Returns:
            Formatted few-shot examples
        """
        examples = self.get_cot_examples()
        return examples.get_few_shot_prompt(max_examples)

    def _get_package_dir(self) -> Path:
        """Get the directory containing this expert's module."""
        import inspect

        module = inspect.getmodule(self.__class__)
        if module and module.__file__:
            return Path(module.__file__).parent
        return Path.cwd()

    def _load_cot_examples(self) -> CoTExamples:
        """Load CoT examples from JSON file."""
        path = self._get_package_dir() / self.cot_examples_file
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            # Parse examples
            examples = []
            for ex in data.get("examples", []):
                examples.append(
                    CoTExample(
                        query=ex["query"],
                        action=VirtualExpertAction(**ex["action"]),
                    )
                )
            return CoTExamples(
                expert_name=self.name,
                examples=examples,
            )
        return CoTExamples(expert_name=self.name, examples=[])

    def _load_schema(self) -> ExpertSchema:
        """Load schema from JSON file."""
        path = self._get_package_dir() / self.schema_file
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            # Parse operations
            operations = {}
            for op_name, op_data in data.get("operations", {}).items():
                params = {}
                for p_name, p_data in op_data.get("parameters", {}).items():
                    params[p_name] = ParameterSchema(**p_data)
                operations[op_name] = OperationSchema(
                    name=op_name,
                    description=op_data.get("description", ""),
                    parameters=params,
                )
            return ExpertSchema(
                name=data.get("name", self.name),
                description=data.get("description", self.description),
                operations=operations,
            )
        return ExpertSchema(name=self.name, description=self.description)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
