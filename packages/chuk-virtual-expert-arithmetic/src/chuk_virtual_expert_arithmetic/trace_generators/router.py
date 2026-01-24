"""
Generator Router.

Routes problem specs to the appropriate trace generator.
"""

from __future__ import annotations

from chuk_virtual_expert_arithmetic.schema.trace import Trace
from chuk_virtual_expert_arithmetic.schema.problem import ProblemSpec, ProblemType
from chuk_virtual_expert_arithmetic.trace_generators.base import TraceGenerator
from chuk_virtual_expert_arithmetic.trace_generators.entity import EntityTraceGenerator
from chuk_virtual_expert_arithmetic.trace_generators.arithmetic import ArithmeticTraceGenerator
from chuk_virtual_expert_arithmetic.trace_generators.comparison import ComparisonTraceGenerator
from chuk_virtual_expert_arithmetic.trace_generators.allocation import AllocationTraceGenerator


# Registry of generators
GENERATORS: list[TraceGenerator] = [
    EntityTraceGenerator(),
    ArithmeticTraceGenerator(),
    ComparisonTraceGenerator(),
    AllocationTraceGenerator(),
]


def route_to_generator(spec: ProblemSpec) -> TraceGenerator | None:
    """
    Find the appropriate generator for a problem spec.

    Args:
        spec: The problem specification

    Returns:
        The generator that can handle this spec, or None
    """
    for generator in GENERATORS:
        if generator.can_handle(spec):
            return generator
    return None


def generate_trace(spec: ProblemSpec) -> Trace | None:
    """
    Generate a trace for a problem spec.

    Convenience function that routes and generates in one call.

    Args:
        spec: The problem specification

    Returns:
        A verifiable trace, or None if no generator can handle the spec
    """
    generator = route_to_generator(spec)
    if generator is None:
        return None
    return generator.generate(spec)


def get_generator_for_type(problem_type: ProblemType) -> TraceGenerator | None:
    """Get generator by problem type."""
    for generator in GENERATORS:
        if problem_type in generator.supported_types:
            return generator
    return None


def supported_problem_types() -> list[ProblemType]:
    """Return all problem types that have generators."""
    types = []
    for generator in GENERATORS:
        types.extend(generator.supported_types)
    return list(set(types))
