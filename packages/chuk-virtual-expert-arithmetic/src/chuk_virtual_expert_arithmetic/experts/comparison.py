"""
ComparisonExpert - handles comparison and difference calculations.

Domain operations: compare (semantic distinction from compute, same mechanics).
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from chuk_virtual_expert.trace_solver import TraceSolverExpert


class ComparisonExpert(TraceSolverExpert):
    """Expert for comparison and difference problems."""

    name: ClassVar[str] = "comparison"
    description: ClassVar[str] = "Computes differences, ratios, and comparisons between quantities"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 11

    cot_examples_file: ClassVar[str] = "../data/cot_examples.json"
    calibration_file: ClassVar[str] = "../data/calibration.json"

    def can_handle(self, prompt: str) -> bool:
        """Check if prompt involves comparison."""
        patterns = [
            r"\bhow many more\b",
            r"\btimes as many\b",
            r"\bdifference\b",
            r"\bcompare\b",
            r"\bmore than\b",
            r"\bless than\b",
            r"\bratio\b",
        ]
        prompt_lower = prompt.lower()
        return any(re.search(p, prompt_lower) for p in patterns)

    def execute_step(self, step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        """Execute comparison-specific operations."""
        op = next(iter(step))

        if op == "compare":
            c = step["compare"]
            op_name = c["op"]
            args = [self.resolve(a, state) for a in c["args"]]
            result = self._compute(op_name, args)
            if "var" in c:
                state[str(c["var"])] = result

        else:
            raise ValueError(f"Unknown comparison operation: {op}")

        return state
