"""Comparison problem generator - typed TraceExample models.

All patterns are strictly 5-step with hybrid var naming:
- First init: entity-anchored (name.item) or descriptive (total) — connects to question text
- Second init: always "factor" — the relationship parameter
- Computes: always "step1" then "result"
- Query: always "result"

One template per pattern for maximum repetition signal.
"""

import random

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    ComputeOp,
    ComputeStep,
    InitStep,
    QueryStep,
)

NAMES = ["Alice", "Bob", "Carol", "Dan", "Emma", "Frank"]
ITEMS = ["stickers", "cards", "marbles", "coins", "books"]


def generate_times_more() -> TraceExample:
    """A has X times as many as B. How many more?"""
    name1, name2 = random.sample(NAMES, 2)
    item = random.choice(ITEMS)
    base = random.randint(5, 20)
    multiplier = random.randint(2, 5)

    difference = base * multiplier - base
    var_base = f"{name2.lower()}.{item}"

    question = f"{name1} has {multiplier} times as many {item} as {name2}. {name2} has {base}. How many more does {name1} have?"

    return TraceExample(
        expert="comparison",
        query=question,
        trace=[
            InitStep(var=var_base, value=base),
            InitStep(var="factor", value=multiplier),
            ComputeStep(compute_op=ComputeOp.MUL, args=[var_base, "factor"], var="step1"),
            ComputeStep(compute_op=ComputeOp.SUB, args=["step1", var_base], var="result"),
            QueryStep(var="result"),
        ],
        answer=difference,
        expected_operation="execute_trace",
    )


def generate_sum_and_difference() -> TraceExample:
    """Together they have X. A has Y more. How many does A have?

    Formula: (total + diff) / 2 = A's amount
    Note: Uses literal 2 in div args (mathematical constant, not extracted value).
    """
    name1, name2 = random.sample(NAMES, 2)
    item = random.choice(ITEMS)

    b = random.randint(10, 30)
    diff = random.randint(5, 15)
    a = b + diff
    total = a + b

    question = f"{name1} and {name2} have {total} {item} together. {name1} has {diff} more than {name2}. How many does {name1} have?"

    return TraceExample(
        expert="comparison",
        query=question,
        trace=[
            InitStep(var="total", value=total),
            InitStep(var="factor", value=diff),
            ComputeStep(compute_op=ComputeOp.ADD, args=["total", "factor"], var="step1"),
            ComputeStep(compute_op=ComputeOp.DIV, args=["step1", 2], var="result"),  # Literal 2 is math constant
            QueryStep(var="result"),
        ],
        answer=a,
        expected_operation="execute_trace",
    )


def generate_more_less() -> TraceExample:
    """A has X more than B. B has Y. Total?"""
    name1, name2 = random.sample(NAMES, 2)
    item = random.choice(ITEMS)

    base = random.randint(10, 30)
    more = random.randint(5, 15)
    amount1 = base + more
    total = amount1 + base

    var_base = f"{name2.lower()}.{item}"

    question = f"{name1} has {more} more {item} than {name2}. {name2} has {base}. How many do they have together?"

    return TraceExample(
        expert="comparison",
        query=question,
        trace=[
            InitStep(var=var_base, value=base),
            InitStep(var="factor", value=more),
            ComputeStep(compute_op=ComputeOp.ADD, args=[var_base, "factor"], var="step1"),
            ComputeStep(compute_op=ComputeOp.ADD, args=["step1", var_base], var="result"),
            QueryStep(var="result"),
        ],
        answer=total,
        expected_operation="execute_trace",
    )


def generate_half_as_many() -> TraceExample:
    """A has half as many as B. B has X. How many more does B have?"""
    name1, name2 = random.sample(NAMES, 2)
    item = random.choice(ITEMS)

    base = random.randint(10, 40) * 2  # Ensure even
    half = base // 2
    var_base = f"{name2.lower()}.{item}"

    question = f"{name1} has half as many {item} as {name2}. {name2} has {base}. How many more does {name2} have?"

    return TraceExample(
        expert="comparison",
        query=question,
        trace=[
            InitStep(var=var_base, value=base),
            InitStep(var="factor", value=2),
            ComputeStep(compute_op=ComputeOp.DIV, args=[var_base, "factor"], var="step1"),
            ComputeStep(compute_op=ComputeOp.SUB, args=[var_base, "step1"], var="result"),
            QueryStep(var="result"),
        ],
        answer=half,
        expected_operation="execute_trace",
    )


GENERATORS = [
    generate_times_more,
    generate_sum_and_difference,
    generate_more_less,
    generate_half_as_many,
]


def generate(n: int = 60) -> list[TraceExample]:
    """Generate n comparison examples (15 per pattern)."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
