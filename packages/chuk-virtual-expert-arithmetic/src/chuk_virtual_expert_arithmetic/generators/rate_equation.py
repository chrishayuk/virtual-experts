"""Rate/equation problem generator - typed TraceExample models.

All patterns are strictly 4-step: init(rate), init(time), compute(mul), query(result).
The model routes and structures; the expert computes. No shape variance.
"""

import random

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    ComputeOp,
    ComputeStep,
    InitStep,
    QueryStep,
)


def generate_rate_time_quantity() -> TraceExample:
    """Rate x time = quantity (production/output)."""
    rate = random.randint(5, 50)
    time = random.randint(2, 12)
    result = rate * time

    scenarios = [
        f"A printer prints {rate} pages per minute. How many pages in {time} minutes?",
        f"A factory makes {rate} widgets per hour. How many in {time} hours?",
        f"A machine produces {rate} items per day. How many in {time} days?",
        f"A bakery bakes {rate} loaves per hour. How many loaves in {time} hours?",
    ]

    question = random.choice(scenarios)

    return TraceExample(
        expert="rate_equation",
        query=question,
        trace=[
            InitStep(var="rate", value=rate),
            InitStep(var="time", value=time),
            ComputeStep(compute_op=ComputeOp.MUL, args=["rate", "time"], var="quantity"),
            QueryStep(var="quantity"),
        ],
        answer=result,
        expected_operation="execute_trace",
    )


def generate_distance_speed_time() -> TraceExample:
    """Distance = speed x time (travel)."""
    speed = random.randint(30, 80)
    time = random.randint(2, 8)
    distance = speed * time

    scenarios = [
        f"A car travels at {speed} km/h. How far does it go in {time} hours?",
        f"A train moves at {speed} mph. What distance does it cover in {time} hours?",
        f"A cyclist rides at {speed} km/h. How many km in {time} hours?",
    ]

    question = random.choice(scenarios)

    return TraceExample(
        expert="rate_equation",
        query=question,
        trace=[
            InitStep(var="speed", value=speed),
            InitStep(var="time", value=time),
            ComputeStep(compute_op=ComputeOp.MUL, args=["speed", "time"], var="distance"),
            QueryStep(var="distance"),
        ],
        answer=distance,
        expected_operation="execute_trace",
    )


def generate_consumption_rate() -> TraceExample:
    """Consumption = rate x time (usage)."""
    rate = random.randint(2, 20)
    time = random.randint(2, 10)
    total = rate * time

    scenarios = [
        f"A car uses {rate} liters of fuel per hour. How many liters in {time} hours?",
        f"A heater burns {rate} units of gas per hour. How much gas in {time} hours?",
        f"A pool loses {rate} gallons per day to evaporation. How many gallons lost in {time} days?",
    ]

    question = random.choice(scenarios)

    return TraceExample(
        expert="rate_equation",
        query=question,
        trace=[
            InitStep(var="rate", value=rate),
            InitStep(var="time", value=time),
            ComputeStep(compute_op=ComputeOp.MUL, args=["rate", "time"], var="total"),
            QueryStep(var="total"),
        ],
        answer=total,
        expected_operation="execute_trace",
    )


def generate_earning_rate() -> TraceExample:
    """Earnings = rate x time (income)."""
    rate = random.randint(8, 50)
    time = random.randint(2, 10)
    total = rate * time

    scenarios = [
        f"A worker earns ${rate} per hour. How much in {time} hours?",
        f"A freelancer charges ${rate} per task. How much for {time} tasks?",
        f"A store sells {rate} items per day. How many items in {time} days?",
    ]

    question = random.choice(scenarios)

    return TraceExample(
        expert="rate_equation",
        query=question,
        trace=[
            InitStep(var="rate", value=rate),
            InitStep(var="time", value=time),
            ComputeStep(compute_op=ComputeOp.MUL, args=["rate", "time"], var="total"),
            QueryStep(var="total"),
        ],
        answer=total,
        expected_operation="execute_trace",
    )


GENERATORS = [
    generate_rate_time_quantity,
    generate_distance_speed_time,
    generate_consumption_rate,
    generate_earning_rate,
]


def generate(n: int = 40) -> list[TraceExample]:
    """Generate n rate equation examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
