"""Compositional problem generator - multi-expert traces.

Each pattern combines two experts: a specialized first step (percentage or rate_equation)
piped into an arithmetic chain via source: prev.result.

All patterns produce exactly 2 sub-traces.
One template per pattern.
"""

from __future__ import annotations

import random
from typing import Any

ITEMS = ["shirt", "jacket", "bag", "book", "toy"]
NAMES = ["Alice", "Bob", "Carol", "Dan", "Emma"]


def generate_percent_off_plus_extra() -> dict[str, Any]:
    """X% off a price, plus extra cost (shipping/tax)."""
    price = random.randint(40, 200)
    percent = random.choice([10, 15, 20, 25, 30])
    extra = random.randint(5, 25)
    item = random.choice(ITEMS)

    sale_price = price * (100 - percent) / 100
    total = sale_price + extra

    question = (
        f"A {item} costs ${price}. It's {percent}% off. Plus ${extra} shipping. What's the total?"
    )

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
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["prev", "factor"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": total,
    }


def generate_percent_increase_minus_cost() -> dict[str, Any]:
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
                    {
                        "op": "compute",
                        "compute_op": "sub",
                        "args": ["prev", "factor"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": gain,
    }


def generate_percent_of_then_multiply() -> dict[str, Any]:
    """X% of Y gives a unit cost, multiply by quantity."""
    whole = random.randint(50, 200)
    percent = random.choice([10, 20, 25, 50])
    quantity = random.randint(2, 8)

    unit = whole * percent / 100
    total = unit * quantity

    item = random.choice(ITEMS)
    question = (
        f"A {item} is priced at {percent}% of ${whole}. You buy {quantity}. What's the total?"
    )

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
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["prev", "factor"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": total,
    }


def generate_rate_then_subtract() -> dict[str, Any]:
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
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["rate", "time"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "prev", "source": "prev.result"},
                    {"op": "init", "var": "factor", "value": defective},
                    {
                        "op": "compute",
                        "compute_op": "sub",
                        "args": ["prev", "factor"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": good,
    }


# =============================================================================
# MULTI-STEP PATTERNS
# =============================================================================


def generate_value_increase_profit() -> dict[str, Any]:
    """Asset value increase: buy + improvement, value increases by X%, calculate profit.

    Pattern: Purchase price + improvement cost, value increases by percentage,
    find profit (new value - total cost).

    Solution: cost = purchase + improvements
              new_value = purchase * (1 + rate/100)
              profit = new_value - cost
    """
    original = random.choice([50000, 60000, 80000, 100000, 120000])
    repairs = random.choice([20000, 30000, 40000, 50000])
    percent = random.choice([50, 75, 100, 125, 150])

    total_cost = original + repairs
    increase = original * percent / 100
    new_value = original + increase
    profit = new_value - total_cost

    name = random.choice(NAMES)
    question = (
        f"{name} buys a house for ${original} and puts in ${repairs} in repairs. "
        f"This increased the value of the house by {percent}%. How much profit did they make?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "percentage",
                "trace": [
                    {"op": "init", "var": "original", "value": original},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_increase", "base": "original", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "new_value", "source": "prev.result"},
                    {"op": "init", "var": "original", "value": original},
                    {"op": "init", "var": "repairs", "value": repairs},
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["original", "repairs"],
                        "var": "step1",
                    },
                    {
                        "op": "compute",
                        "compute_op": "sub",
                        "args": ["new_value", "step1"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": profit,
    }


def generate_paired_discount() -> dict[str, Any]:
    """Every second item discounted: full price + discounted price per pair.

    Pattern: First item full price, second item at X% of price.
    Total cost for N items where N is even.

    Solution: discounted = full_price * rate/100
              pair_cost = full_price + discounted
              pairs = quantity / 2
              total = pairs * pair_cost
    """
    full_price = random.choice([4, 5, 6, 8, 10])
    discount_percent = random.choice([50, 60, 70, 75, 80])
    quantity = random.choice([8, 10, 12, 14, 16, 18, 20])

    discounted = full_price * discount_percent / 100
    pair_cost = full_price + discounted
    pairs = quantity // 2
    total = pairs * pair_cost

    items = ["glasses", "cups", "plates", "bowls", "mugs"]
    item = random.choice(items)
    name = random.choice(NAMES)

    question = (
        f"{name} wants to buy {item}. One costs ${full_price}, but every second one "
        f"costs only {discount_percent}% of the price. {name} wants to buy {quantity}. "
        f"How much does it cost?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "percentage",
                "trace": [
                    {"op": "init", "var": "full_price", "value": full_price},
                    {"op": "init", "var": "rate", "value": discount_percent},
                    {"op": "percent_of", "base": "full_price", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "discounted", "source": "prev.result"},
                    {"op": "init", "var": "full_price", "value": full_price},
                    {"op": "init", "var": "pairs", "value": pairs},
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["full_price", "discounted"],
                        "var": "step1",
                    },
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["step1", "pairs"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": total,
    }


def generate_interrupted_rate() -> dict[str, Any]:
    """Interrupted process: partial progress, delay, then restart from beginning.

    Pattern: Processing X units at Y units/time. After Z% progress, interruption
    requires delay then restart from beginning. Find total time.

    Solution: partial_time = (total * percent/100) / rate
              full_time = total / rate
              total_time = partial_time + delay + full_time
    """
    total_size = random.choice([100, 150, 200, 250, 300])
    rate = random.choice([2, 4, 5, 10])
    progress_percent = random.choice([20, 25, 30, 40, 50])
    delay = random.choice([10, 15, 20, 25, 30])

    partial_size = total_size * progress_percent / 100
    partial_time = partial_size / rate
    full_time = total_size / rate
    total_time = partial_time + delay + full_time

    name = random.choice(NAMES)
    question = (
        f"{name} is downloading a {total_size} GB file at {rate} GB/minute. "
        f"{progress_percent}% of the way through, a restart is required which takes {delay} minutes. "
        f"Then the download starts from the beginning. How long does it take in total?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "percentage",
                "trace": [
                    {"op": "init", "var": "total_size", "value": total_size},
                    {"op": "init", "var": "rate", "value": progress_percent},
                    {"op": "percent_of", "base": "total_size", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "partial_size", "source": "prev.result"},
                    {"op": "init", "var": "speed", "value": rate},
                    {"op": "init", "var": "delay", "value": delay},
                    {"op": "init", "var": "total_size", "value": total_size},
                    {
                        "op": "compute",
                        "compute_op": "div",
                        "args": ["partial_size", "speed"],
                        "var": "step1",
                    },
                    {
                        "op": "compute",
                        "compute_op": "div",
                        "args": ["total_size", "speed"],
                        "var": "step2",
                    },
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["step1", "delay"],
                        "var": "step3",
                    },
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["step3", "step2"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": total_time,
    }


def generate_consume_then_sell() -> dict[str, Any]:
    """Consume some items, sell remainder at a price.

    GSM-8K pattern: "Janet's ducks lay 16 eggs. She eats 3, bakes with 4,
    sells rest at $2 each. How much does she make?"

    Solution: remaining = 16 - 3 - 4 = 9
              revenue = 9 * 2 = 18
    """
    initial = random.randint(15, 30)
    consume1 = random.randint(2, 5)
    consume2 = random.randint(2, 5)
    price = random.randint(2, 5)

    remaining = initial - consume1 - consume2
    revenue = remaining * price

    name = random.choice(NAMES)
    animals = ["ducks", "chickens", "hens"]
    animal = random.choice(animals)

    question = (
        f"{name}'s {animal} lay {initial} eggs per day. "
        f"They eat {consume1} for breakfast and use {consume2} for baking. "
        f"They sell the rest at ${price} each. How much do they make?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "entity_track",
                "trace": [
                    {"op": "init", "var": "eggs", "value": initial},
                    {"op": "consume", "entity": "eggs", "amount": consume1},
                    {"op": "consume", "entity": "eggs", "amount": consume2},
                    {"op": "query", "var": "eggs"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "remaining", "source": "prev.result"},
                    {"op": "init", "var": "price", "value": price},
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["remaining", "price"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": revenue,
    }


# =============================================================================
# COMPLEX 3-EXPERT COMPOSITION PATTERNS
# =============================================================================


def generate_cost_increase_profit() -> dict[str, Any]:
    """Full profit calculation: cost calculation + value increase + profit.

    3-expert chain with multi-value wiring:
    Sub 0: arithmetic (cost = purchase + improvements)
    Sub 1: percentage (new_value = purchase * (1 + rate/100))
    Sub 2: arithmetic (profit = new_value - cost) — uses sub0.result and prev.result
    """
    purchase = random.choice([40000, 50000, 60000, 80000, 100000])
    repairs = random.choice([15000, 20000, 30000, 40000, 50000])
    percent = random.choice([50, 75, 100, 125, 150])

    total_cost = purchase + repairs
    new_value = purchase * (100 + percent) / 100
    profit = new_value - total_cost

    name = random.choice(NAMES)
    question = (
        f"{name} buys a house for ${purchase} and spends ${repairs} on repairs. "
        f"This increased the value of the house by {percent}%. How much profit did {name} make?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "purchase", "value": purchase},
                    {"op": "init", "var": "repairs", "value": repairs},
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["purchase", "repairs"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "percentage",
                "trace": [
                    {"op": "init", "var": "base", "value": purchase},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_increase", "base": "base", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "new_value", "source": "prev.result"},
                    {"op": "init", "var": "cost", "source": "sub0.result"},
                    {
                        "op": "compute",
                        "compute_op": "sub",
                        "args": ["new_value", "cost"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": profit,
    }


def generate_comparison_then_total() -> dict[str, Any]:
    """Comparison chain then sum: A has X, B has N times A, C has M times B. Total?

    GSM-8K pattern: "Toulouse has twice as many sheep as Charleston.
    Charleston has 4× Seattle's. Seattle has 20. Total together?"

    Solution: seattle=20, charleston=4*20=80, toulouse=2*80=160, total=260

    Simplified to single arithmetic trace with interleaved inits (was 3-expert, now 1-expert).
    """
    base = random.randint(10, 30)
    mult1 = random.choice([2, 3, 4, 5])
    mult2 = random.choice([2, 3, 4])

    mid = base * mult1
    top = mid * mult2
    total = base + mid + top

    names = ["Seattle", "Portland", "Denver", "Austin", "Boston"]
    random.shuffle(names)
    name_base, name_mid, name_top = names[:3]

    question = (
        f"{name_top} has {mult2} times as many sheep as {name_mid}. "
        f"{name_mid} has {mult1} times as many sheep as {name_base}. "
        f"{name_base} has {base} sheep. How many sheep do they have together?"
    )

    # Single arithmetic trace with interleaved computation
    return {
        "query": question,
        "expert": "arithmetic",
        "trace": [
            {"op": "init", "var": "base", "value": base},
            {"op": "init", "var": "mult1", "value": mult1},
            {"op": "compute", "compute_op": "mul", "args": ["base", "mult1"], "var": "step1"},
            {"op": "init", "var": "mult2", "value": mult2},  # interleaved init
            {"op": "compute", "compute_op": "mul", "args": ["step1", "mult2"], "var": "step2"},
            {"op": "compute", "compute_op": "add", "args": ["base", "step1"], "var": "step3"},
            {"op": "compute", "compute_op": "add", "args": ["step3", "step2"], "var": "result"},
            {"op": "query", "var": "result"},
        ],
        "answer": total,
    }


def generate_rate_comparison_total() -> dict[str, Any]:
    """Rate calculation then comparison: A produces X/hr, B produces N times A. Total in T hours?

    Pattern: "Machine A makes 10 widgets/hour. Machine B makes 3× as many.
    How many widgets total in 5 hours?"

    Solution: A=10*5=50, B=3*10*5=150, total=200

    Simplified to single arithmetic trace with interleaved inits (was 3-expert, now 1-expert).
    """
    rate_a = random.randint(5, 20)
    multiplier = random.choice([2, 3, 4])
    hours = random.randint(4, 10)

    output_a = rate_a * hours
    rate_b = rate_a * multiplier
    output_b = rate_b * hours
    total = output_a + output_b

    question = (
        f"Machine A produces {rate_a} items per hour. Machine B produces {multiplier} times as many. "
        f"How many items do both machines produce together in {hours} hours?"
    )

    # Single arithmetic trace: rate_a*hours + (rate_a*mult)*hours
    return {
        "query": question,
        "expert": "arithmetic",
        "trace": [
            {"op": "init", "var": "rate_a", "value": rate_a},
            {"op": "init", "var": "hours", "value": hours},
            {"op": "compute", "compute_op": "mul", "args": ["rate_a", "hours"], "var": "step1"},
            {"op": "init", "var": "multiplier", "value": multiplier},  # interleaved init
            {"op": "compute", "compute_op": "mul", "args": ["rate_a", "multiplier"], "var": "step2"},
            {"op": "compute", "compute_op": "mul", "args": ["step2", "hours"], "var": "step3"},
            {"op": "compute", "compute_op": "add", "args": ["step1", "step3"], "var": "result"},
            {"op": "query", "var": "result"},
        ],
        "answer": total,
    }


def generate_discount_tax_total() -> dict[str, Any]:
    """Discount then tax: original price → discounted → with tax added.

    Pattern: "A $100 item is 20% off. Then 10% tax is added. Final price?"

    Solution: discounted = 100 * 0.8 = 80, tax = 80 * 0.1 = 8, total = 88
    """
    original = random.choice([50, 80, 100, 120, 150])
    discount_pct = random.choice([10, 15, 20, 25, 30])
    tax_pct = random.choice([5, 8, 10, 12])

    discounted = original * (100 - discount_pct) / 100
    tax = discounted * tax_pct / 100
    final = discounted + tax

    item = random.choice(ITEMS)
    question = (
        f"A {item} originally costs ${original}. It's {discount_pct}% off. "
        f"Then {tax_pct}% tax is added. What's the final price?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": "percentage",
                "trace": [
                    {"op": "init", "var": "original", "value": original},
                    {"op": "init", "var": "rate", "value": discount_pct},
                    {"op": "percent_off", "base": "original", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "percentage",
                "trace": [
                    {"op": "init", "var": "base", "source": "prev.result"},
                    {"op": "init", "var": "rate", "value": tax_pct},
                    {"op": "percent_of", "base": "base", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": "arithmetic",
                "trace": [
                    {"op": "init", "var": "tax", "source": "prev.result"},
                    {"op": "init", "var": "discounted", "source": "sub0.result"},
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["discounted", "tax"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": final,
    }


GENERATORS = [
    # Basic 2-expert patterns (percentage → arithmetic)
    generate_percent_off_plus_extra,
    generate_percent_increase_minus_cost,
    generate_percent_of_then_multiply,
    generate_rate_then_subtract,
    # Multi-step 2-expert patterns
    generate_value_increase_profit,  # Value increase → calculate profit
    generate_paired_discount,  # Alternating discount pricing
    generate_interrupted_rate,  # Partial progress + restart
    generate_consume_then_sell,  # Entity track → revenue
    # Complex 3-expert patterns with multi-value wiring
    generate_cost_increase_profit,  # Cost + value increase + profit (uses sub0.result)
    generate_comparison_then_total,  # Chain comparisons → sum all
    generate_rate_comparison_total,  # Two rates → total output
    generate_discount_tax_total,  # Discount → tax → final price
]


def generate(n: int = 40) -> list[dict[str, Any]]:
    """Generate n compositional examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
