"""
RateEquationExpert - handles rate and formula-based problems.

Uses common operations + recognizes formula annotation.
Problems like: "Driving at 60km/h for 2.5 hours, what distance?"
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from chuk_virtual_expert.trace_solver import TraceSolverExpert


class RateEquationExpert(TraceSolverExpert):
    """Expert for rate and formula-based problems."""

    name: ClassVar[str] = "rate_equation"
    description: ClassVar[str] = "Solves rate/formula problems (speed, distance, time, work)"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 11

    cot_examples_file: ClassVar[str] = "../data/cot_examples.json"
    calibration_file: ClassVar[str] = "../data/calibration.json"

    def can_handle(self, prompt: str) -> bool:
        """Check if prompt involves rate or formula problems."""
        patterns = [
            r"\bper\s+hour\b",
            r"\bper\s+minute\b",
            r"\brate\b",
            r"\bspeed\b",
            r"\bkm/h\b",
            r"\bmph\b",
            r"\bm/s\b",
            r"\bdistance\b",
            r"\bvelocity\b",
            r"\bwork\s+rate\b",
        ]
        prompt_lower = prompt.lower()
        return any(re.search(p, prompt_lower) for p in patterns)

    def execute_step(self, step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        """No extra domain ops beyond common ones - formula is handled by base."""
        op = next(iter(step))
        raise ValueError(f"Unknown rate_equation operation: {op}")
