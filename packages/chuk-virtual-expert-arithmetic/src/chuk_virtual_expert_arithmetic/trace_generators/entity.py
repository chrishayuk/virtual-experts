"""
Entity Tracking Trace Generator.

Handles problems where entities have values that change through operations.

Examples:
- "Jenny has 5 apples. She gives 2 to Bob. How many does Jenny have?"
- "Tom has 10 marbles. He loses 3 and finds 2. How many does he have?"
"""

from __future__ import annotations

from decimal import Decimal

from chuk_virtual_expert_arithmetic.schema.problem import OperationType, ProblemSpec, ProblemType
from chuk_virtual_expert_arithmetic.schema.trace import Trace, TraceBuilder
from chuk_virtual_expert_arithmetic.trace_generators.base import TraceGenerator


class EntityTraceGenerator(TraceGenerator):
    """
    Generator for entity tracking problems.

    These problems involve:
    - One or more entities with initial values
    - Operations that modify entity values (add, subtract, transfer)
    - A query for a specific entity's final value
    """

    @property
    def supported_types(self) -> list[ProblemType]:
        return [ProblemType.ENTITY_TRACKING]

    def generate(self, spec: ProblemSpec) -> Trace:
        """Generate trace by initializing entities and applying operations."""
        builder = TraceBuilder(problem_type="entity_tracking")

        # Step 1: Initialize all entities
        for entity in spec.entities:
            if entity.initial_value is not None:
                builder.init(entity.name, entity.initial_value)
            else:
                builder.init(entity.name, Decimal(0))

        # Step 2: Apply operations in sequence
        for op in spec.operations:
            if op.type == OperationType.ADD:
                if op.amount is not None:
                    builder.add(op.target, op.amount)

            elif op.type == OperationType.SUBTRACT:
                if op.amount is not None:
                    builder.subtract(op.target, op.amount)

            elif op.type == OperationType.TRANSFER:
                if op.source and op.amount is not None:
                    builder.transfer(op.source, op.target, op.amount)

            elif op.type == OperationType.MULTIPLY:
                if op.factor is not None:
                    builder.multiply(op.target, op.factor)

            elif op.type == OperationType.DIVIDE:
                if op.factor is not None:
                    builder.divide(op.target, op.factor)

        # Step 3: Query the target
        if spec.query:
            builder.query(spec.query.target)

        return builder.build()
