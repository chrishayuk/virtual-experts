"""Compositional problem generator - multi-expert traces.

Each pattern combines two experts: a specialized first step (percentage or rate_equation)
piped into an arithmetic chain via source: prev.result.

All patterns produce exactly 2 sub-traces.
One template per pattern.
"""

import random


ITEMS = ["shirt", "jacket", "bag", "book", "toy"]
NAMES = ["Alice", "Bob", "Carol", "Dan", "Emma"]


def generate_percent_off_plus_extra() -> dict:
    """X% off a price, plus extra cost (shipping/tax)."""
    price = random.randint(40, 200)
    percent = random.choice([10, 15, 20, 25, 30])
    extra = random.randint(5, 25)
    item = random.choice(ITEMS)

    sale_price = price * (100 - percent) / 100
    total = sale_price + extra

    question = f"A {item} costs ${price}. It's {percent}% off. Plus ${extra} shipping. What's the total?"

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "percentage",
                "trace": [
                    {"op": "init", "var": "price", "value": price},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_off", "base": "price", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "prev", "source": "prev.result"},
                    {"op": "init", "var": "factor", "value": extra},
                    {"op": "compute", "compute_op": "add", "args": ["prev", "factor"], "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": total,
    }


def generate_percent_increase_minus_cost() -> dict:
    """Stock increases by X%, subtract original to find gain."""
    original = random.randint(50, 200)
    percent = random.choice([10, 20, 25, 50])

    new_value = original * (100 + percent) / 100
    gain = new_value - original

    question = f"A stock worth ${original} increases by {percent}%. How much did you gain?"

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "percentage",
                "trace": [
                    {"op": "init", "var": "base", "value": original},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_increase", "base": "base", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "prev", "source": "prev.result"},
                    {"op": "init", "var": "factor", "value": original},
                    {"op": "compute", "compute_op": "sub", "args": ["prev", "factor"], "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": gain,
    }


def generate_percent_of_then_multiply() -> dict:
    """X% of Y gives a unit cost, multiply by quantity."""
    whole = random.randint(50, 200)
    percent = random.choice([10, 20, 25, 50])
    quantity = random.randint(2, 8)

    unit = whole * percent / 100
    total = unit * quantity

    item = random.choice(ITEMS)
    question = f"A {item} is priced at {percent}% of ${whole}. You buy {quantity}. What's the total?"

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "percentage",
                "trace": [
                    {"op": "init", "var": "whole", "value": whole},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_of", "base": "whole", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "prev", "source": "prev.result"},
                    {"op": "init", "var": "factor", "value": quantity},
                    {"op": "compute", "compute_op": "mul", "args": ["prev", "factor"], "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": total,
    }


def generate_rate_then_subtract() -> dict:
    """Rate x time gives total, subtract defective/used."""
    rate = random.randint(5, 30)
    time = random.randint(2, 10)
    defective = random.randint(2, min(15, rate * time - 1))

    total = rate * time
    good = total - defective

    question = f"A machine makes {rate} items per hour for {time} hours. {defective} are defective. How many good items?"

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "rate_equation",
                "trace": [
                    {"op": "init", "var": "rate", "value": rate},
                    {"op": "init", "var": "time", "value": time},
                    {"op": "compute", "compute_op": "mul", "args": ["rate", "time"], "var": "quantity"},
                    {"op": "query", "var": "quantity"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "prev", "source": "prev.result"},
                    {"op": "init", "var": "factor", "value": defective},
                    {"op": "compute", "compute_op": "sub", "args": ["prev", "factor"], "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": good,
    }


GENERATORS = [
    generate_percent_off_plus_extra,
    generate_percent_increase_minus_cost,
    generate_percent_of_then_multiply,
    generate_rate_then_subtract,
]


def generate(n: int = 40) -> list[dict]:
    """Generate n compositional examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
