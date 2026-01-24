"""
PercentageExpert - handles percentage-based calculations.

Domain operations: percent_off, percent_increase, percent_of.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from chuk_virtual_expert.trace_solver import TraceSolverExpert


class PercentageExpert(TraceSolverExpert):
    """Expert for percentage calculation problems."""

    name: ClassVar[str] = "percentage"
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

    def execute_step(self, step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        """Execute percentage-specific operations."""
        op = next(iter(step))

        if op == "percent_off":
            p = step["percent_off"]
            base_val = self.resolve(p["base"], state)
            rate = self.resolve(p["rate"], state)
            result = base_val * (1 - rate / 100)
            if "var" in p:
                state[str(p["var"])] = result

        elif op == "percent_increase":
            p = step["percent_increase"]
            base_val = self.resolve(p["base"], state)
            rate = self.resolve(p["rate"], state)
            result = base_val * (1 + rate / 100)
            if "var" in p:
                state[str(p["var"])] = result

        elif op == "percent_of":
            p = step["percent_of"]
            base_val = self.resolve(p["base"], state)
            rate = self.resolve(p["rate"], state)
            result = base_val * rate / 100
            if "var" in p:
                state[str(p["var"])] = result

        else:
            raise ValueError(f"Unknown percentage operation: {op}")

        return state
