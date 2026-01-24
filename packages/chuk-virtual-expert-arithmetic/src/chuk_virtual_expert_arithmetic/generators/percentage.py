"""Percentage problem generator - typed TraceExample models."""

import random

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    ComputeOp,
    ComputeStep,
    InitStep,
    PercentIncreaseStep,
    PercentOffStep,
    QueryStep,
)


def generate_percent_off() -> TraceExample:
    """X% off a price."""
    price = random.randint(20, 200)
    percent = random.choice([10, 15, 20, 25, 30, 40, 50])
    final = price * (100 - percent) / 100

    item = random.choice(["shirt", "book", "toy", "jacket", "bag"])

    question = f"A {item} costs ${price}. It's {percent}% off. What's the sale price?"

    return TraceExample(
        expert="percentage",
        query=question,
        trace=[
            InitStep(var="price", value=price),
            InitStep(var="discount_rate", value=percent),
            PercentOffStep(base="price", rate="discount_rate", var="sale_price"),
            QueryStep(var="sale_price"),
        ],
        answer=final,
        expected_operation="execute_trace",
    )


def generate_percent_increase() -> TraceExample:
    """X% increase."""
    base = random.randint(50, 200)
    percent = random.choice([10, 15, 20, 25, 50])
    final = base * (100 + percent) / 100

    scenarios = [
        f"A stock worth ${base} increases by {percent}%. What's the new value?",
        f"Rent of ${base} goes up {percent}%. What's the new rent?",
        f"A salary of ${base} gets a {percent}% raise. What's the new salary?",
    ]

    question = random.choice(scenarios)

    return TraceExample(
        expert="percentage",
        query=question,
        trace=[
            InitStep(var="base", value=base),
            InitStep(var="increase_rate", value=percent),
            PercentIncreaseStep(base="base", rate="increase_rate", var="final"),
            QueryStep(var="final"),
        ],
        answer=final,
        expected_operation="execute_trace",
    )


def generate_tip_calculation() -> TraceExample:
    """Calculate tip on a bill."""
    bill = random.randint(20, 100)
    tip_percent = random.choice([15, 18, 20, 25])
    tip = bill * tip_percent / 100
    total = bill + tip

    question = f"Your bill is ${bill}. You want to leave a {tip_percent}% tip. What's the total including tip?"

    return TraceExample(
        expert="percentage",
        query=question,
        trace=[
            InitStep(var="bill", value=bill),
            InitStep(var="tip_rate", value=tip_percent),
            ComputeStep(compute_op=ComputeOp.MUL, args=["bill", "tip_rate"], var="tip_times_100"),
            ComputeStep(compute_op=ComputeOp.DIV, args=["tip_times_100", 100], var="tip"),
            ComputeStep(compute_op=ComputeOp.ADD, args=["bill", "tip"], var="total"),
            QueryStep(var="total"),
        ],
        answer=total,
        expected_operation="execute_trace",
    )


def generate_simple_percent() -> TraceExample:
    """What is X% of Y?"""
    whole = random.randint(50, 200)
    percent = random.choice([10, 20, 25, 50, 75])
    part = whole * percent / 100

    question = f"What is {percent}% of {whole}?"

    return TraceExample(
        expert="percentage",
        query=question,
        trace=[
            InitStep(var="whole", value=whole),
            InitStep(var="percent", value=percent),
            ComputeStep(compute_op=ComputeOp.MUL, args=["whole", "percent"], var="times_100"),
            ComputeStep(compute_op=ComputeOp.DIV, args=["times_100", 100], var="result"),
            QueryStep(var="result"),
        ],
        answer=part,
        expected_operation="execute_trace",
    )


GENERATORS = [
    generate_percent_off,
    generate_percent_increase,
    generate_tip_calculation,
    generate_simple_percent,
]


def generate(n: int = 15) -> list[TraceExample]:
    """Generate n percentage examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
