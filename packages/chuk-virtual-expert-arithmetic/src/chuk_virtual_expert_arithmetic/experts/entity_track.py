"""
EntityTrackExpert - tracks entity quantities through transfers, consumption, and additions.

Handles problems like: "Alice has 16 eggs. She gives 3 to Bob and eats 4.
She sells the rest at $2 each. How much revenue?"
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from chuk_virtual_expert.trace_solver import TraceSolverExpert


class EntityTrackExpert(TraceSolverExpert):
    """Expert for entity state tracking problems."""

    name: ClassVar[str] = "entity_track"
    description: ClassVar[str] = "Tracks entity quantities through transfers and operations"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 15

    # Override data file paths to point to data/ directory
    cot_examples_file: ClassVar[str] = "../data/cot_examples.json"
    calibration_file: ClassVar[str] = "../data/calibration.json"

    def can_handle(self, prompt: str) -> bool:
        """Check if prompt involves entity tracking."""
        patterns = [
            r"\bgives\b",
            r"\bhas\s+\d+\s+\w+",
            r"\bloses\b",
            r"\beats?\b",
            r"\btransfers?\b",
            r"\bremaining\b",
            r"\bleft\b",
        ]
        prompt_lower = prompt.lower()
        return any(re.search(p, prompt_lower) for p in patterns)

    def execute_step(self, step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        """Execute entity-specific operations."""
        op = next(iter(step))

        if op == "transfer":
            t = step["transfer"]
            from_e = str(t["from"])
            to_e = str(t["to"])
            amount = self.resolve(t["amount"], state)

            if from_e not in state:
                state[from_e] = 0.0
            if to_e not in state:
                state[to_e] = 0.0

            if state[from_e] < amount - self.tolerance:
                raise ValueError(f"Insufficient {from_e} for transfer ({state[from_e]} < {amount})")

            state[from_e] -= amount
            state[to_e] += amount

        elif op == "consume":
            c = step["consume"]
            entity = str(c["entity"])
            amount = self.resolve(c["amount"], state)

            if entity not in state:
                raise ValueError(f"Entity {entity} not initialized")
            if state[entity] < amount - self.tolerance:
                raise ValueError(f"Insufficient {entity} for consume ({state[entity]} < {amount})")

            state[entity] -= amount

        elif op == "add":
            a = step["add"]
            entity = str(a["entity"])
            amount = self.resolve(a["amount"], state)

            if entity not in state:
                state[entity] = 0.0
            state[entity] += amount

        else:
            raise ValueError(f"Unknown entity_track operation: {op}")

        return state
