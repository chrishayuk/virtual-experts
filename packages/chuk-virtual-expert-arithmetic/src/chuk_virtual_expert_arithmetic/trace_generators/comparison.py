"""
Comparison Trace Generator.

Handles problems asking "how many more/less" between entities.

Examples:
- "Tom has 15, Jane has 5. How many more does Tom have than Jane?"
- "Alice has 3 times as many as Bob. Bob has 5. How many more does Alice have?"
"""

from __future__ import annotations

from decimal import Decimal

from chuk_virtual_expert_arithmetic.trace_generators.base import TraceGenerator
from chuk_virtual_expert_arithmetic.schema.trace import Trace, TraceBuilder
from chuk_virtual_expert_arithmetic.schema.problem import ProblemSpec, ProblemType, OperationType


class ComparisonTraceGenerator(TraceGenerator):
    """
    Generator for comparison problems.

    These problems involve:
    - Two or more entities with values
    - Computing the difference or ratio between them
    - A query for how many more/less one has than another
    """

    @property
    def supported_types(self) -> list[ProblemType]:
        return [ProblemType.COMPARISON]

    def generate(self, spec: ProblemSpec) -> Trace:
        """Generate trace by initializing entities and computing difference."""
        builder = TraceBuilder(problem_type="comparison")

        # Step 1: Initialize all entities
        for entity in spec.entities:
            if entity.initial_value is not None:
                builder.init(entity.name, entity.initial_value)

        # Step 2: Apply any operations (e.g., "Tom has 3 times as many as Jane")
        for op in spec.operations:
            if op.type == OperationType.MULTIPLY:
                if op.factor is not None:
                    builder.multiply(op.target, op.factor)
            elif op.type == OperationType.ADD:
                if op.amount is not None:
                    builder.add(op.target, op.amount)

        # Step 3: Compute comparison if query is a comparison
        if spec.query and spec.query.question == "compare":
            entity_a = spec.query.compare_a
            entity_b = spec.query.compare_b
            if entity_a and entity_b:
                builder.compare(entity_a, entity_b, "difference")
                builder.query("difference")
            else:
                builder.query(spec.query.target)
        elif spec.query:
            builder.query(spec.query.target)

        return builder.build()
