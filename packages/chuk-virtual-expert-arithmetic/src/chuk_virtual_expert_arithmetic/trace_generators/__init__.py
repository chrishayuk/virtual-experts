"""
Trace Generators for arithmetic virtual experts.

Convert ProblemSpec into verifiable Trace objects.
"""

from chuk_virtual_expert_arithmetic.trace_generators.allocation import AllocationTraceGenerator
from chuk_virtual_expert_arithmetic.trace_generators.arithmetic import ArithmeticTraceGenerator
from chuk_virtual_expert_arithmetic.trace_generators.base import TraceGenerator
from chuk_virtual_expert_arithmetic.trace_generators.comparison import ComparisonTraceGenerator
from chuk_virtual_expert_arithmetic.trace_generators.entity import EntityTraceGenerator
from chuk_virtual_expert_arithmetic.trace_generators.router import (
    generate_trace,
    get_generator_for_type,
    route_to_generator,
    supported_problem_types,
)

__all__ = [
    "TraceGenerator",
    "EntityTraceGenerator",
    "ArithmeticTraceGenerator",
    "ComparisonTraceGenerator",
    "AllocationTraceGenerator",
    "route_to_generator",
    "generate_trace",
    "get_generator_for_type",
    "supported_problem_types",
]
