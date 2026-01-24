"""Comparison problem generator - typed TraceExample models."""

import random

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    ComputeOp,
    ComputeStep,
    FormulaStep,
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

    larger = base * multiplier
    difference = larger - base

    question = f"{name1} has {multiplier} times as many {item} as {name2}. {name2} has {base}. How many more does {name1} have than {name2}?"

    var2 = f"{name2.lower()}.{item}"
    var1 = f"{name1.lower()}.{item}"

    return TraceExample(
        expert="comparison",
        query=question,
        trace=[
            InitStep(var=var2, value=base),
            InitStep(var="multiplier", value=multiplier),
            ComputeStep(compute_op=ComputeOp.MUL, args=[var2, "multiplier"], var=var1),
            ComputeStep(compute_op=ComputeOp.SUB, args=[var1, var2], var="difference"),
            QueryStep(var="difference"),
        ],
        answer=difference,
        expected_operation="execute_trace",
    )


def generate_sum_and_difference() -> TraceExample:
    """Together they have X. A has Y more than B. How many does A have?"""
    name1, name2 = random.sample(NAMES, 2)
    item = random.choice(ITEMS)

    b = random.randint(10, 30)
    diff = random.randint(5, 15)
    a = b + diff
    total = a + b

    question = f"{name1} and {name2} have {total} {item} together. {name1} has {diff} more than {name2}. How many does {name1} have?"

    var1 = f"{name1.lower()}.{item}"
    var2 = f"{name2.lower()}.{item}"

    return TraceExample(
        expert="comparison",
        query=question,
        trace=[
            InitStep(var="total", value=total),
            InitStep(var="difference", value=diff),
            FormulaStep(expression=f"{name1.lower()} + {name2.lower()} = total"),
            FormulaStep(expression=f"{name1.lower()} = {name2.lower()} + difference"),
            ComputeStep(compute_op=ComputeOp.SUB, args=["total", "difference"], var="twice_b"),
            ComputeStep(compute_op=ComputeOp.DIV, args=["twice_b", 2], var=var2),
            ComputeStep(compute_op=ComputeOp.ADD, args=[var2, "difference"], var=var1),
            QueryStep(var=var1),
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

    question = f"{name1} has {more} more {item} than {name2}. {name2} has {base}. How many do they have together?"

    var1 = f"{name1.lower()}.{item}"
    var2 = f"{name2.lower()}.{item}"

    return TraceExample(
        expert="comparison",
        query=question,
        trace=[
            InitStep(var=var2, value=base),
            InitStep(var="more", value=more),
            ComputeStep(compute_op=ComputeOp.ADD, args=[var2, "more"], var=var1),
            ComputeStep(compute_op=ComputeOp.ADD, args=[var1, var2], var="total"),
            QueryStep(var="total"),
        ],
        answer=total,
        expected_operation="execute_trace",
    )


def generate_half_as_many() -> TraceExample:
    """A has half as many as B. B has X. How many does A have?"""
    name1, name2 = random.sample(NAMES, 2)
    item = random.choice(ITEMS)

    base = random.randint(10, 40) * 2  # Ensure even
    half = base // 2

    question = f"{name1} has half as many {item} as {name2}. {name2} has {base}. How many does {name1} have?"

    var1 = f"{name1.lower()}.{item}"
    var2 = f"{name2.lower()}.{item}"

    return TraceExample(
        expert="comparison",
        query=question,
        trace=[
            InitStep(var=var2, value=base),
            ComputeStep(compute_op=ComputeOp.DIV, args=[var2, 2], var=var1),
            QueryStep(var=var1),
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


def generate(n: int = 40) -> list[TraceExample]:
    """Generate n comparison examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
