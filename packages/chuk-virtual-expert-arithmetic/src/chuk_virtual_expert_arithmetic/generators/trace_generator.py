"""
TraceGenerator - generates synthetic trace training examples.

Produces (query, trace, expected_answer) tuples for training
the CoT rewriter to produce valid traces.
"""

from __future__ import annotations

import random
from typing import Any


class TraceGenerator:
    """Generates synthetic arithmetic trace examples for training."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def generate_entity_track(self, n: int = 10) -> list[dict[str, Any]]:
        """Generate entity tracking examples."""
        examples = []
        for _ in range(n):
            entity = self._rng.choice(["eggs", "apples", "cookies", "books", "dollars"])
            initial = self._rng.randint(10, 100)
            consume1 = self._rng.randint(1, initial // 3)
            consume2 = self._rng.randint(1, initial // 3)
            remaining = initial - consume1 - consume2

            trace = [
                {"init": entity, "value": initial},
                {"consume": {"entity": entity, "amount": consume1}},
                {"consume": {"entity": entity, "amount": consume2}},
                {"query": entity},
            ]

            examples.append(
                {
                    "expert": "entity_track",
                    "trace": trace,
                    "expected_answer": remaining,
                }
            )
        return examples

    def generate_arithmetic(self, n: int = 10) -> list[dict[str, Any]]:
        """Generate pure arithmetic examples."""
        examples = []
        for _ in range(n):
            a = self._rng.randint(1, 100)
            b = self._rng.randint(1, 100)
            op = self._rng.choice(["add", "sub", "mul"])

            if op == "add":
                answer = a + b
            elif op == "sub":
                answer = a - b
            else:
                answer = a * b

            trace = [
                {"init": "a", "value": a},
                {"init": "b", "value": b},
                {"compute": {"op": op, "args": ["a", "b"], "var": "result"}},
                {"query": "result"},
            ]

            examples.append(
                {
                    "expert": "arithmetic",
                    "trace": trace,
                    "expected_answer": answer,
                }
            )
        return examples

    def generate_percentage(self, n: int = 10) -> list[dict[str, Any]]:
        """Generate percentage examples."""
        examples = []
        for _ in range(n):
            base = self._rng.choice([50, 100, 150, 200, 250, 500])
            rate = self._rng.choice([5, 10, 15, 20, 25, 30, 50])
            op_type = self._rng.choice(["percent_off", "percent_increase"])

            if op_type == "percent_off":
                answer = base * (1 - rate / 100)
            else:
                answer = base * (1 + rate / 100)

            trace = [
                {"init": "base", "value": base},
                {"init": "rate", "value": rate},
                {op_type: {"base": "base", "rate": "rate", "var": "result"}},
                {"query": "result"},
            ]

            examples.append(
                {
                    "expert": "percentage",
                    "trace": trace,
                    "expected_answer": answer,
                }
            )
        return examples

    def generate_rate_equation(self, n: int = 10) -> list[dict[str, Any]]:
        """Generate rate/formula examples."""
        examples = []
        for _ in range(n):
            rate = self._rng.choice([30, 40, 50, 60, 80, 100, 120])
            time = self._rng.choice([0.5, 1, 1.5, 2, 2.5, 3, 4, 5])
            answer = rate * time

            trace = [
                {"given": {"rate": rate, "time": time}},
                {"formula": "result = rate * time"},
                {"compute": {"op": "mul", "args": ["rate", "time"], "var": "result"}},
                {"query": "result"},
            ]

            examples.append(
                {
                    "expert": "rate_equation",
                    "trace": trace,
                    "expected_answer": answer,
                }
            )
        return examples

    def generate_comparison(self, n: int = 10) -> list[dict[str, Any]]:
        """Generate comparison examples."""
        examples = []
        for _ in range(n):
            a = self._rng.randint(10, 100)
            multiplier = self._rng.randint(2, 5)
            b = a * multiplier
            difference = b - a

            trace = [
                {"init": "a", "value": a},
                {"compute": {"op": "mul", "args": ["a", multiplier], "var": "b"}},
                {"compare": {"op": "sub", "args": ["b", "a"], "var": "difference"}},
                {"query": "difference"},
            ]

            examples.append(
                {
                    "expert": "comparison",
                    "trace": trace,
                    "expected_answer": difference,
                }
            )
        return examples

    def generate_all(self, n_per_type: int = 10) -> list[dict[str, Any]]:
        """Generate examples for all expert types."""
        examples = []
        examples.extend(self.generate_entity_track(n_per_type))
        examples.extend(self.generate_arithmetic(n_per_type))
        examples.extend(self.generate_percentage(n_per_type))
        examples.extend(self.generate_rate_equation(n_per_type))
        examples.extend(self.generate_comparison(n_per_type))
        self._rng.shuffle(examples)
        return examples
