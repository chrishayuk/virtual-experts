"""Arithmetic chain problem generator - typed TraceExample models."""

import random

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import ComputeOp, ComputeStep, InitStep, QueryStep


def generate_price_chain() -> TraceExample:
    """Price + tax + shipping pattern."""
    base = random.randint(10, 100)
    tax = round(random.uniform(1, 10), 2)
    shipping = random.randint(2, 10)

    total = round(base + tax + shipping, 2)
    item = random.choice(["toy", "book", "shirt", "gadget", "tool"])

    question = (
        f"A {item} costs ${base}. Tax adds ${tax}. Shipping is ${shipping}. What's the total?"
    )

    return TraceExample(
        expert="arithmetic",
        query=question,
        trace=[
            InitStep(var="price", value=base),
            InitStep(var="tax", value=tax),
            InitStep(var="shipping", value=shipping),
            ComputeStep(compute_op=ComputeOp.ADD, args=["price", "tax"], var="with_tax"),
            ComputeStep(compute_op=ComputeOp.ADD, args=["with_tax", "shipping"], var="total"),
            QueryStep(var="total"),
        ],
        answer=total,
        expected_operation="execute_trace",
    )


def generate_subtract_chain() -> TraceExample:
    """Start with amount, subtract multiple times."""
    start = random.randint(50, 200)
    sub1 = random.randint(5, 30)
    sub2 = random.randint(5, 30)
    sub3 = random.randint(5, 20)

    final = start - sub1 - sub2 - sub3

    question = f"You have ${start}. You spend ${sub1} on lunch, ${sub2} on a ticket, and ${sub3} on snacks. How much do you have left?"

    return TraceExample(
        expert="arithmetic",
        query=question,
        trace=[
            InitStep(var="money", value=start),
            InitStep(var="lunch", value=sub1),
            InitStep(var="ticket", value=sub2),
            InitStep(var="snacks", value=sub3),
            ComputeStep(compute_op=ComputeOp.SUB, args=["money", "lunch"], var="after_lunch"),
            ComputeStep(
                compute_op=ComputeOp.SUB, args=["after_lunch", "ticket"], var="after_ticket"
            ),
            ComputeStep(compute_op=ComputeOp.SUB, args=["after_ticket", "snacks"], var="remaining"),
            QueryStep(var="remaining"),
        ],
        answer=final,
        expected_operation="execute_trace",
    )


def generate_multiply_add() -> TraceExample:
    """Multiply then add."""
    count = random.randint(3, 10)
    price = random.randint(5, 20)
    extra = random.randint(5, 20)

    total = count * price + extra
    item = random.choice(["pens", "notebooks", "bottles", "bags"])

    question = f"You buy {count} {item} at ${price} each and pay ${extra} for gift wrapping. What's the total?"

    return TraceExample(
        expert="arithmetic",
        query=question,
        trace=[
            InitStep(var="count", value=count),
            InitStep(var="price", value=price),
            InitStep(var="wrapping", value=extra),
            ComputeStep(compute_op=ComputeOp.MUL, args=["count", "price"], var="subtotal"),
            ComputeStep(compute_op=ComputeOp.ADD, args=["subtotal", "wrapping"], var="total"),
            QueryStep(var="total"),
        ],
        answer=total,
        expected_operation="execute_trace",
    )


def generate_divide_multiply() -> TraceExample:
    """Divide then multiply."""
    divisor = random.choice([2, 4, 5, 10])
    per_item = random.randint(5, 25)
    total = per_item * divisor  # Ensure exact division
    multiplier = random.randint(2, 5)

    final = per_item * multiplier

    if multiplier == 3:
        mult_text = "triples"
    elif multiplier == 2:
        mult_text = "doubles"
    else:
        mult_text = f"multiplies by {multiplier}"

    question = f"You split ${total} equally among {divisor} people. Each person {mult_text} their share. How much does each have?"

    return TraceExample(
        expert="arithmetic",
        query=question,
        trace=[
            InitStep(var="total", value=total),
            InitStep(var="people", value=divisor),
            InitStep(var="multiplier", value=multiplier),
            ComputeStep(compute_op=ComputeOp.DIV, args=["total", "people"], var="per_person"),
            ComputeStep(compute_op=ComputeOp.MUL, args=["per_person", "multiplier"], var="final"),
            QueryStep(var="final"),
        ],
        answer=final,
        expected_operation="execute_trace",
    )


GENERATORS = [
    generate_price_chain,
    generate_subtract_chain,
    generate_multiply_add,
    generate_divide_multiply,
]


def generate(n: int = 40) -> list[TraceExample]:
    """Generate n arithmetic examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
