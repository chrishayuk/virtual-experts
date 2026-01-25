"""Percentage problem generator - typed TraceExample models.

All patterns are strictly 4-step: init, init, domain_op, query.
One template per pattern.
"""

import random

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    InitStep,
    PercentIncreaseStep,
    PercentOffStep,
    PercentOfStep,
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
            InitStep(var="rate", value=percent),
            PercentOffStep(base="price", rate="rate", var="result"),
            QueryStep(var="result"),
        ],
        answer=final,
        expected_operation="execute_trace",
    )


def generate_percent_increase() -> TraceExample:
    """X% increase."""
    base = random.randint(50, 200)
    percent = random.choice([10, 15, 20, 25, 50])
    final = base * (100 + percent) / 100

    question = f"A stock worth ${base} increases by {percent}%. What's the new value?"

    return TraceExample(
        expert="percentage",
        query=question,
        trace=[
            InitStep(var="base", value=base),
            InitStep(var="rate", value=percent),
            PercentIncreaseStep(base="base", rate="rate", var="result"),
            QueryStep(var="result"),
        ],
        answer=final,
        expected_operation="execute_trace",
    )


def generate_tip_calculation() -> TraceExample:
    """Calculate tip amount on a bill."""
    bill = random.randint(20, 100)
    tip_percent = random.choice([15, 18, 20, 25])
    tip = bill * tip_percent / 100

    question = f"Your bill is ${bill}. You leave a {tip_percent}% tip. How much is the tip?"

    return TraceExample(
        expert="percentage",
        query=question,
        trace=[
            InitStep(var="bill", value=bill),
            InitStep(var="rate", value=tip_percent),
            PercentOfStep(base="bill", rate="rate", var="result"),
            QueryStep(var="result"),
        ],
        answer=tip,
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
            InitStep(var="rate", value=percent),
            PercentOfStep(base="whole", rate="rate", var="result"),
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


def generate(n: int = 30) -> list[TraceExample]:
    """Generate n percentage examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
