"""
ArithmeticExpert - handles pure arithmetic chain problems.

Only uses common operations (init, compute, query) from TraceSolverExpert.
No domain-specific operations needed.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from chuk_virtual_expert.trace_models import BaseTraceStep
from chuk_virtual_expert.trace_solver import TraceSolverExpert


class ArithmeticExpert(TraceSolverExpert):
    """Expert for pure arithmetic chain problems."""

    name: ClassVar[str] = "arithmetic"
    description: ClassVar[str] = "Computes arithmetic chains (cost totals, sums, products)"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 10

    cot_examples_file: ClassVar[str] = "../data/cot_examples.json"
    calibration_file: ClassVar[str] = "../data/calibration.json"

    def can_handle(self, prompt: str) -> bool:
        """Check if prompt is a pure arithmetic problem."""
        patterns = [
            r"\bcosts?\b",
            r"\btotal\b",
            r"\bhow much\b",
            r"\bprice\b",
            r"\bsum\b",
            r"\bproduct\b",
            r"\d+\s*[\+\-\*\/]\s*\d+",
        ]
        prompt_lower = prompt.lower()
        return any(re.search(p, prompt_lower) for p in patterns)

    async def execute_step(self, step: BaseTraceStep, state: dict[str, Any]) -> dict[str, Any]:
        """No domain-specific operations - raises for unknown steps."""
        raise ValueError(f"Unknown arithmetic step type: {type(step).__name__}")
