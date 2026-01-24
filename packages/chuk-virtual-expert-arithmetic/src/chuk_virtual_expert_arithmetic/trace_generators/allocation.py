"""
Allocation Trace Generator.

Handles constraint-based allocation problems.

Examples:
- "Split $100 between Alice and Bob. Alice gets twice what Bob gets."
- "Sum of two numbers is 30. One is 4 more than the other."
"""

from __future__ import annotations

from decimal import Decimal

from chuk_virtual_expert_arithmetic.schema.problem import ProblemSpec, ProblemType
from chuk_virtual_expert_arithmetic.schema.trace import Trace, TraceBuilder
from chuk_virtual_expert_arithmetic.trace_generators.base import TraceGenerator


class AllocationTraceGenerator(TraceGenerator):
    """
    Generator for allocation problems.

    These problems involve:
    - Multiple entities
    - Constraints (sum, ratio, difference)
    - Need to solve for entity values

    Supports:
    - Two entities with sum constraint and ratio constraint
    - Two entities with sum constraint and difference constraint
    """

    @property
    def supported_types(self) -> list[ProblemType]:
        return [ProblemType.ALLOCATION, ProblemType.RATE_EQUATION]

    def generate(self, spec: ProblemSpec) -> Trace:
        """Solve constraints and generate trace."""
        builder = TraceBuilder(problem_type="allocation")

        # Extract constraints
        sum_constraint = None
        ratio_constraint = None
        diff_constraint = None

        for c in spec.constraints:
            if c.type == "sum":
                sum_constraint = c
            elif c.type == "ratio":
                ratio_constraint = c
            elif c.type == "difference":
                diff_constraint = c

        # Solve based on constraint types
        if sum_constraint and ratio_constraint:
            # Sum = S, A = k * B
            # A + B = S -> k*B + B = S -> B = S / (k+1)
            total = sum_constraint.value or Decimal(0)
            ratio = ratio_constraint.factor or Decimal(1)

            entities = sum_constraint.entities
            if len(entities) >= 2:
                if ratio_constraint.entities and len(ratio_constraint.entities) >= 2:
                    larger = ratio_constraint.entities[0]
                    smaller = ratio_constraint.entities[1]
                else:
                    larger = entities[0]
                    smaller = entities[1]

                smaller_val = total / (ratio + 1)
                larger_val = ratio * smaller_val

                builder.init(smaller, smaller_val)
                builder.init(larger, larger_val)

        elif sum_constraint and diff_constraint:
            # A + B = S, A - B = D
            # A = (S + D) / 2, B = (S - D) / 2
            total = sum_constraint.value or Decimal(0)
            diff = diff_constraint.value or Decimal(0)

            entities = sum_constraint.entities
            if len(entities) >= 2:
                entity_a = entities[0]
                entity_b = entities[1]

                val_a = (total + diff) / 2
                val_b = (total - diff) / 2

                builder.init(entity_a, val_a)
                builder.init(entity_b, val_b)

        else:
            # Just initialize entities with their values
            for entity in spec.entities:
                if entity.initial_value is not None:
                    builder.init(entity.name, entity.initial_value)

        # Query
        if spec.query:
            builder.query(spec.query.target)

        return builder.build()
