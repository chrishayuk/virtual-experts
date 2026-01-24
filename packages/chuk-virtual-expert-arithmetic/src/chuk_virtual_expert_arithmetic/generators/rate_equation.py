"""Rate/equation problem generator - typed TraceExample models."""

import random

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    ComputeOp,
    ComputeStep,
    FormulaStep,
    InitStep,
    QueryStep,
)


def generate_rate_time_quantity() -> TraceExample:
    """Rate x time = quantity."""
    rate = random.randint(5, 50)
    time = random.randint(2, 12)
    result = rate * time

    scenarios = [
        (f"A printer prints {rate} pages per minute. How many pages in {time} minutes?", "pages"),
        (f"A factory makes {rate} widgets per hour. How many in {time} hours?", "widgets"),
        (f"A runner covers {rate} meters per minute. How far in {time} minutes?", "meters"),
        (f"A machine produces {rate} items per day. How many in {time} days?", "items"),
    ]

    question, unit = random.choice(scenarios)

    return TraceExample(
        expert="rate_equation",
        query=question,
        trace=[
            InitStep(var="rate", value=rate),
            InitStep(var="time", value=time),
            FormulaStep(expression="quantity = rate * time"),
            ComputeStep(compute_op=ComputeOp.MUL, args=["rate", "time"], var="quantity"),
            QueryStep(var="quantity"),
        ],
        answer=result,
        expected_operation="execute_trace",
    )


def generate_distance_speed_time() -> TraceExample:
    """Distance = speed x time."""
    speed = random.randint(30, 80)
    time = random.randint(2, 8)
    distance = speed * time

    question = f"A car travels at {speed} km/h. How far does it go in {time} hours?"

    return TraceExample(
        expert="rate_equation",
        query=question,
        trace=[
            InitStep(var="speed", value=speed),
            InitStep(var="time", value=time),
            FormulaStep(expression="distance = speed * time"),
            ComputeStep(compute_op=ComputeOp.MUL, args=["speed", "time"], var="distance"),
            QueryStep(var="distance"),
        ],
        answer=distance,
        expected_operation="execute_trace",
    )


def generate_work_rate() -> TraceExample:
    """Work = rate x time, then divide."""
    workers = random.randint(2, 5)
    time = random.randint(2, 6)
    # Make rate a multiple of workers so total_work divides evenly
    rate = workers * random.randint(3, 8)
    total_work = rate * time
    per_worker = total_work // workers

    question = f"A team does {rate} tasks per hour. After {time} hours, they split the work among {workers} people. How many tasks per person?"

    return TraceExample(
        expert="rate_equation",
        query=question,
        trace=[
            InitStep(var="rate", value=rate),
            InitStep(var="time", value=time),
            InitStep(var="workers", value=workers),
            ComputeStep(compute_op=ComputeOp.MUL, args=["rate", "time"], var="total"),
            ComputeStep(compute_op=ComputeOp.DIV, args=["total", "workers"], var="per_worker"),
            QueryStep(var="per_worker"),
        ],
        answer=per_worker,
        expected_operation="execute_trace",
    )


def generate_combined_rate() -> TraceExample:
    """Two rates combined."""
    rate1 = random.randint(5, 20)
    rate2 = random.randint(5, 20)
    time = random.randint(2, 6)

    total = (rate1 + rate2) * time

    question = f"Machine A produces {rate1} items/hour. Machine B produces {rate2} items/hour. How many total in {time} hours?"

    return TraceExample(
        expert="rate_equation",
        query=question,
        trace=[
            InitStep(var="rate_a", value=rate1),
            InitStep(var="rate_b", value=rate2),
            InitStep(var="time", value=time),
            ComputeStep(compute_op=ComputeOp.ADD, args=["rate_a", "rate_b"], var="combined_rate"),
            ComputeStep(compute_op=ComputeOp.MUL, args=["combined_rate", "time"], var="total"),
            QueryStep(var="total"),
        ],
        answer=total,
        expected_operation="execute_trace",
    )


GENERATORS = [
    generate_rate_time_quantity,
    generate_distance_speed_time,
    generate_work_rate,
    generate_combined_rate,
]


def generate(n: int = 40) -> list[TraceExample]:
    """Generate n rate equation examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
