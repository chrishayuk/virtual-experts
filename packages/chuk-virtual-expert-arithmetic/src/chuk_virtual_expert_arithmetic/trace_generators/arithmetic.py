"""
Arithmetic Chain Trace Generator.

Handles problems with sequential arithmetic operations on a single value.

Examples:
- "Start with 10, add 5, multiply by 2"
- "A pizza has 8 slices. 3 people each eat 2 slices. How many left?"
- "6 bags with 4 oranges each. How many oranges total?"
"""

from __future__ import annotations

from decimal import Decimal

from chuk_virtual_expert_arithmetic.trace_generators.base import TraceGenerator
from chuk_virtual_expert_arithmetic.schema.trace import Trace, TraceBuilder
from chuk_virtual_expert_arithmetic.schema.problem import ProblemSpec, ProblemType, OperationType


class ArithmeticTraceGenerator(TraceGenerator):
    """
    Generator for arithmetic chain problems.

    These problems involve:
    - A starting value (explicit or implicit)
    - A sequence of arithmetic operations
    - A query for the final result
    """

    @property
    def supported_types(self) -> list[ProblemType]:
        return [ProblemType.ARITHMETIC_CHAIN, ProblemType.PERCENTAGE]

    def generate(self, spec: ProblemSpec) -> Trace:
        """Generate trace by applying operations in sequence."""
        builder = TraceBuilder(problem_type=spec.problem_type.value)

        # Determine the main variable name
        if spec.entities:
            main_var = spec.entities[0].name
            initial = spec.entities[0].initial_value or Decimal(0)
        else:
            main_var = "result"
            initial = Decimal(0)

        # Initialize
        builder.init(main_var, initial)

        # Apply operations
        for op in spec.operations:
            target = op.target or main_var

            if op.type == OperationType.ADD:
                if op.amount is not None:
                    builder.add(target, op.amount)

            elif op.type == OperationType.SUBTRACT:
                if op.amount is not None:
                    builder.subtract(target, op.amount)

            elif op.type == OperationType.MULTIPLY:
                if op.factor is not None:
                    builder.multiply(target, op.factor)
                elif op.amount is not None:
                    builder.multiply(target, op.amount)

            elif op.type == OperationType.DIVIDE:
                if op.factor is not None:
                    builder.divide(target, op.factor)
                elif op.amount is not None:
                    builder.divide(target, op.amount)

        # Query
        query_target = spec.query.target if spec.query else main_var
        builder.query(query_target)

        return builder.build()
