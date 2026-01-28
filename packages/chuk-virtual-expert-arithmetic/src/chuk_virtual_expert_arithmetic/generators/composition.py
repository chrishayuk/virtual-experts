"""Compositional problem generator - multi-expert traces.

Each pattern combines two experts: a specialized first step (percentage or rate_equation)
piped into an arithmetic chain via source: prev.result.

All patterns produce exactly 2 sub-traces.
One template per pattern.
"""

from __future__ import annotations

import random
from typing import Any

from chuk_virtual_expert_arithmetic.types import ExpertType
from chuk_virtual_expert_arithmetic.vocab import get_vocab

# Vocab singleton for random sampling
_vocab = get_vocab()


def generate_percent_off_plus_extra() -> dict[str, Any]:
    """X% off a price, plus extra cost (shipping/tax)."""
    price = random.randint(40, 200)
    percent = random.choice([10, 15, 20, 25, 30])
    extra = random.randint(5, 25)
    item = _vocab.random("items.countable_singular")

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
                "expert": ExpertType.PERCENTAGE.value,
                "trace": [
                    {"op": "init", "var": "price", "value": price},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_off", "base": "price", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
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
                "expert": ExpertType.PERCENTAGE.value,
                "trace": [
                    {"op": "init", "var": "base", "value": original},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_increase", "base": "base", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
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

    item = _vocab.random("items.countable_singular")
    question = (
        f"A {item} is priced at {percent}% of ${whole}. You buy {quantity}. What's the total?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": ExpertType.PERCENTAGE.value,
                "trace": [
                    {"op": "init", "var": "whole", "value": whole},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_of", "base": "whole", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
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
                "expert": ExpertType.RATE_EQUATION.value,
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
                "expert": ExpertType.ARITHMETIC.value,
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

    name = _vocab.random("names.people")
    question = (
        f"{name} buys a house for ${original} and puts in ${repairs} in repairs. "
        f"This increased the value of the house by {percent}%. How much profit did they make?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": ExpertType.PERCENTAGE.value,
                "trace": [
                    {"op": "init", "var": "original", "value": original},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_increase", "base": "original", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
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

    item = _vocab.random("items.countable_plural") or "items"
    name = _vocab.random("names.people")

    # Multiple template variations to improve robustness
    templates = [
        (
            f"{name} wants to buy {item}. One costs ${full_price}, but every second one "
            f"costs only {discount_percent}% of the price. {name} wants to buy {quantity}. "
            f"How much does it cost?"
        ),
        (
            f"{name} went to the store to buy {item}. One {item[:-1] if item.endswith('s') else item} "
            f"costs ${full_price}, but every second {item[:-1] if item.endswith('s') else item} costs "
            f"only {discount_percent}% of the price. {name} wants to buy {quantity} {item}. "
            f"How much does {name} need to pay for them?"
        ),
        (
            f"At a shop, {item} are on a special deal. One costs ${full_price}, and every second one "
            f"costs {discount_percent}% of that price. {name} buys {quantity} {item}. "
            f"What is the total cost?"
        ),
        (
            f"{name} is buying {item} for a party. Each costs ${full_price}, but if you buy two, "
            f"the second one is only {discount_percent}% of the regular price. "
            f"How much does {name} pay for {quantity} {item}?"
        ),
    ]
    question = random.choice(templates)

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": ExpertType.PERCENTAGE.value,
                "trace": [
                    {"op": "init", "var": "full_price", "value": full_price},
                    {"op": "init", "var": "rate", "value": discount_percent},
                    {"op": "percent_of", "base": "full_price", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
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

    name = _vocab.random("names.people")

    # Multiple templates with varied domains
    templates = [
        # Download scenarios
        (
            f"{name} is downloading a {total_size} GB file. The download speed is {rate} GB/minute. "
            f"After {progress_percent}% of the download completes, a restart is required which takes "
            f"{delay} minutes. Then the download starts over from the beginning. "
            f"How long does the entire process take?"
        ),
        (
            f"{name} downloads a {total_size} GB file at a rate of {rate} GB per minute. "
            f"{progress_percent}% through the download, the computer restarts, adding a {delay}-minute delay. "
            f"The download then restarts from scratch. What is the total download time?"
        ),
        # Alternative phrasing (download scenario)
        (
            f"{name} is downloading a {total_size} GB file. Normally they can download {rate} GB/minute, "
            f"but {progress_percent}% of the way through the download, the system forces a restart "
            f"to install updates, which takes {delay} minutes. Then {name} has to restart the download "
            f"from the beginning. How long does it take to download the file?"
        ),
        # Printing/copying scenarios
        (
            f"A printer is printing {total_size} pages at {rate} pages per minute. "
            f"After {progress_percent}% of the job is done, a paper jam causes a {delay}-minute delay "
            f"and the print job restarts from the beginning. How many minutes to complete?"
        ),
        (
            f"{name} is copying {total_size} files at a rate of {rate} files per minute. "
            f"When {progress_percent}% done, an error requires a {delay}-minute restart from zero. "
            f"What is the total time to copy all files?"
        ),
        # Manufacturing scenarios
        (
            f"A factory is producing {total_size} units at {rate} units per minute. "
            f"After {progress_percent}% are made, a malfunction causes a {delay}-minute shutdown "
            f"and production restarts from scratch. Total production time in minutes?"
        ),
        # Reading/processing scenarios
        (
            f"{name} is reading a {total_size}-page document at {rate} pages per minute. "
            f"After finishing {progress_percent}% of it, they realize they need to restart from page 1. "
            f"This costs a {delay}-minute break. How long until {name} finishes the document?"
        ),
    ]
    question = random.choice(templates)

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": ExpertType.PERCENTAGE.value,
                "trace": [
                    {"op": "init", "var": "total_size", "value": total_size},
                    {"op": "init", "var": "rate", "value": progress_percent},
                    {"op": "percent_of", "base": "total_size", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
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

    Pattern: "Ducks lay 16 eggs. Eat 3, bake with 4, sell rest at $2 each."

    Solution: remaining = 16 - 3 - 4 = 9
              revenue = 9 * 2 = 18
    """
    initial = random.randint(15, 30)
    consume1 = random.randint(2, 5)
    consume2 = random.randint(2, 5)
    price = random.randint(2, 5)

    remaining = initial - consume1 - consume2
    revenue = remaining * price

    name = _vocab.random("names.people")
    # Get poultry animal that produces eggs
    farm_animal = _vocab.random("animals.farm_animals")
    animal = farm_animal.get("name", "chickens") if isinstance(farm_animal, dict) else "chickens"

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
                "expert": ExpertType.ENTITY_TRACK.value,
                "trace": [
                    {"op": "init", "var": "eggs", "value": initial},
                    {"op": "consume", "entity": "eggs", "amount": consume1},
                    {"op": "consume", "entity": "eggs", "amount": consume2},
                    {"op": "query", "var": "eggs"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
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

    name = _vocab.random("names.people")
    question = (
        f"{name} buys a house for ${purchase} and spends ${repairs} on repairs. "
        f"This increased the value of the house by {percent}%. How much profit did {name} make?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": ExpertType.ARITHMETIC.value,
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
                "expert": ExpertType.PERCENTAGE.value,
                "trace": [
                    {"op": "init", "var": "base", "value": purchase},
                    {"op": "init", "var": "rate", "value": percent},
                    {"op": "percent_increase", "base": "base", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
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

    item = _vocab.random("items.countable_singular")
    question = (
        f"A {item} originally costs ${original}. It's {discount_pct}% off. "
        f"Then {tax_pct}% tax is added. What's the final price?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": ExpertType.PERCENTAGE.value,
                "trace": [
                    {"op": "init", "var": "original", "value": original},
                    {"op": "init", "var": "rate", "value": discount_pct},
                    {"op": "percent_off", "base": "original", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.PERCENTAGE.value,
                "trace": [
                    {"op": "init", "var": "base", "source": "prev.result"},
                    {"op": "init", "var": "rate", "value": tax_pct},
                    {"op": "percent_of", "base": "base", "rate": "rate", "var": "result"},
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
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


def generate_comparison_then_total() -> dict[str, Any]:
    """Compare prices then calculate total: comparison → arithmetic → total.

    Pattern: "Item A costs $X, Item B costs $Y more. Buy 3 of each. Total cost?"

    3-expert chain:
    Sub 0: comparison (find B's price = A + difference)
    Sub 1: arithmetic (cost_A = A * qty)
    Sub 2: arithmetic (total = cost_A + B_price * qty)
    """
    price_a = random.choice([10, 15, 20, 25, 30])
    difference = random.choice([5, 8, 10, 12, 15])
    quantity = random.choice([2, 3, 4, 5])

    price_b = price_a + difference
    cost_a = price_a * quantity
    cost_b = price_b * quantity
    total = cost_a + cost_b

    item_a = random.choice(["shirt", "book", "toy"])
    item_b = random.choice(["jacket", "bag", "game"])
    name = _vocab.random("names.people")

    question = (
        f"A {item_a} costs ${price_a}. A {item_b} costs ${difference} more than the {item_a}. "
        f"{name} buys {quantity} of each. What's the total cost?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": ExpertType.COMPARISON.value,
                "trace": [
                    {"op": "init", "var": "price_a", "value": price_a},
                    {"op": "init", "var": "difference", "value": difference},
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["price_a", "difference"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
                "trace": [
                    {"op": "init", "var": "price_a", "value": price_a},
                    {"op": "init", "var": "quantity", "value": quantity},
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["price_a", "quantity"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
                "trace": [
                    {"op": "init", "var": "cost_a", "source": "prev.result"},
                    {"op": "init", "var": "price_b", "source": "sub0.result"},
                    {"op": "init", "var": "quantity", "value": quantity},
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["price_b", "quantity"],
                        "var": "step1",
                    },
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["cost_a", "step1"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": total,
    }


def generate_rate_comparison_total() -> dict[str, Any]:
    """Rate calculation then comparison then total.

    Pattern: "Machine A makes X/hour. Machine B makes Y more/hour.
    Both run for Z hours. Total items made?"

    3-expert chain:
    Sub 0: rate_equation (output_A = rate_A * time)
    Sub 1: comparison (rate_B = rate_A + difference)
    Sub 2: arithmetic (total = output_A + rate_B * time)
    """
    rate_a = random.choice([5, 8, 10, 12, 15])
    difference = random.choice([2, 3, 4, 5])
    hours = random.choice([3, 4, 5, 6, 8])

    rate_b = rate_a + difference
    output_a = rate_a * hours
    output_b = rate_b * hours
    total = output_a + output_b

    question = (
        f"Machine A produces {rate_a} items per hour. Machine B produces {difference} more "
        f"items per hour than Machine A. Both machines run for {hours} hours. "
        f"How many items are produced in total?"
    )

    return {
        "query": question,
        "composed": True,
        "steps": [
            {
                "expert": ExpertType.RATE_EQUATION.value,
                "trace": [
                    {"op": "init", "var": "rate", "value": rate_a},
                    {"op": "init", "var": "time", "value": hours},
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
                "expert": ExpertType.COMPARISON.value,
                "trace": [
                    {"op": "init", "var": "rate_a", "value": rate_a},
                    {"op": "init", "var": "difference", "value": difference},
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["rate_a", "difference"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
            {
                "expert": ExpertType.ARITHMETIC.value,
                "trace": [
                    {"op": "init", "var": "output_a", "source": "sub0.result"},
                    {"op": "init", "var": "rate_b", "source": "prev.result"},
                    {"op": "init", "var": "time", "value": hours},
                    {
                        "op": "compute",
                        "compute_op": "mul",
                        "args": ["rate_b", "time"],
                        "var": "step1",
                    },
                    {
                        "op": "compute",
                        "compute_op": "add",
                        "args": ["output_a", "step1"],
                        "var": "result",
                    },
                    {"op": "query", "var": "result"},
                ],
            },
        ],
        "answer": total,
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
    generate_discount_tax_total,  # Discount → tax → final price
    generate_comparison_then_total,  # Compare prices → calculate totals
    generate_rate_comparison_total,  # Rate calculation → comparison → total
]


def generate(n: int = 40) -> list[dict[str, Any]]:
    """Generate n compositional examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
