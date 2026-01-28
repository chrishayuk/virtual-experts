"""
PercentageExpert - handles percentage-based calculations.

Domain operations: percent_off, percent_increase, percent_of.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from chuk_virtual_expert.trace_models import (
    BaseTraceStep,
    PercentIncreaseStep,
    PercentOffStep,
    PercentOfStep,
)
from chuk_virtual_expert.trace_solver import TraceSolverExpert

from chuk_virtual_expert_arithmetic.types import ExpertType


class PercentageExpert(TraceSolverExpert):
    """Expert for percentage calculation problems."""

    name: ClassVar[str] = ExpertType.PERCENTAGE
    description: ClassVar[str] = "Computes percentage discounts, increases, and proportions"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 12

    cot_examples_file: ClassVar[str] = "../data/cot_examples.json"
    calibration_file: ClassVar[str] = "../data/calibration.json"

    def can_handle(self, prompt: str) -> bool:
        """Check if prompt involves percentage calculations."""
        patterns = [
            r"\d+\s*%",
            r"\bpercent\b",
            r"\bdiscount\b",
            r"\boff\b.*\bprice\b",
            r"\bincrease\s+by\b",
            r"\bdecrease\s+by\b",
            r"\bmarkup\b",
            r"\bmarkdown\b",
        ]
        prompt_lower = prompt.lower()
        return any(re.search(p, prompt_lower) for p in patterns)

    async def execute_step(self, step: BaseTraceStep, state: dict[str, Any]) -> dict[str, Any]:
        """Execute percentage-specific operations."""
        if isinstance(step, PercentOffStep):
            base_val = self.resolve(step.base, state)
            rate = self.resolve(step.rate, state)
            result = base_val * (1 - rate / 100)
            if step.var is not None:
                state[step.var] = result

        elif isinstance(step, PercentIncreaseStep):
            base_val = self.resolve(step.base, state)
            rate = self.resolve(step.rate, state)
            result = base_val * (1 + rate / 100)
            if step.var is not None:
                state[step.var] = result

        elif isinstance(step, PercentOfStep):
            base_val = self.resolve(step.base, state)
            rate = self.resolve(step.rate, state)
            result = base_val * rate / 100
            if step.var is not None:
                state[step.var] = result

        else:
            raise ValueError(f"Unknown percentage step type: {type(step).__name__}")

        return state
