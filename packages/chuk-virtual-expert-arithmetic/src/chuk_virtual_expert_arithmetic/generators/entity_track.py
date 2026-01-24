"""Entity tracking problem generator - typed TraceExample models."""

import random

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    AddEntityStep,
    ComputeOp,
    ComputeStep,
    ConsumeStep,
    InitStep,
    QueryStep,
    TransferStep,
)

NAMES = ["Alice", "Bob", "Carol", "Dan", "Emma", "Frank", "Grace", "Henry"]
ITEMS = ["apples", "marbles", "books", "coins", "cards", "stickers", "pencils", "cookies"]
GIVE_VERBS = ["gives", "hands", "passes", "transfers"]
LOSE_VERBS = ["loses", "drops", "misplaces"]
FIND_VERBS = ["finds", "discovers", "picks up"]
EAT_VERBS = ["eats", "consumes", "uses"]


def generate_simple_transfer() -> TraceExample:
    """A gives B some items."""
    name1, name2 = random.sample(NAMES, 2)
    item = random.choice(ITEMS)
    initial = random.randint(10, 50)
    transfer = random.randint(1, initial - 1)
    verb = random.choice(GIVE_VERBS)

    question = f"{name1} has {initial} {item}. {name1} {verb} {transfer} to {name2}. How many {item} does {name1} have?"

    from_var = f"{name1.lower()}.{item}"
    to_var = f"{name2.lower()}.{item}"

    return TraceExample(
        expert="entity_track",
        query=question,
        trace=[
            InitStep(var=from_var, value=initial),
            TransferStep(from_entity=from_var, to_entity=to_var, amount=transfer),
            QueryStep(var=from_var),
        ],
        answer=initial - transfer,
        expected_operation="execute_trace",
    )


def generate_consume_sequence() -> TraceExample:
    """Entity consumes items multiple times."""
    name = random.choice(NAMES)
    item = random.choice(ITEMS)
    initial = random.randint(15, 40)
    consume1 = random.randint(1, initial // 3)
    consume2 = random.randint(1, initial // 3)
    verb1 = random.choice(EAT_VERBS)
    verb2 = random.choice(EAT_VERBS)

    remaining = initial - consume1 - consume2

    question = f"{name} has {initial} {item}. {name} {verb1} {consume1} and then {verb2} {consume2}. How many {item} does {name} have left?"

    return TraceExample(
        expert="entity_track",
        query=question,
        trace=[
            InitStep(var=item, value=initial),
            ConsumeStep(entity=item, amount=consume1),
            ConsumeStep(entity=item, amount=consume2),
            QueryStep(var=item),
        ],
        answer=remaining,
        expected_operation="execute_trace",
    )


def generate_consume_then_multiply() -> TraceExample:
    """Classic GSM-8K pattern: consume then multiply remaining."""
    name = random.choice(NAMES)
    item = random.choice(ITEMS)
    initial = random.randint(10, 30)
    consume1 = random.randint(1, initial // 4)
    consume2 = random.randint(1, initial // 4)
    multiplier = random.randint(2, 5)

    remaining = initial - consume1 - consume2
    final = remaining * multiplier

    verb1 = random.choice(EAT_VERBS)
    verb2 = random.choice(EAT_VERBS)

    question = f"{name} has {initial} {item}. {name} {verb1} {consume1} and {verb2} {consume2}. {name} sells the rest for ${multiplier} each. How much money does {name} make?"

    return TraceExample(
        expert="entity_track",
        query=question,
        trace=[
            InitStep(var=item, value=initial),
            ConsumeStep(entity=item, amount=consume1),
            ConsumeStep(entity=item, amount=consume2),
            ComputeStep(compute_op=ComputeOp.MUL, args=[item, multiplier], var="revenue"),
            QueryStep(var="revenue"),
        ],
        answer=final,
        expected_operation="execute_trace",
    )


def generate_bidirectional_transfer() -> TraceExample:
    """A gives to B, B gives back some."""
    name1, name2 = random.sample(NAMES, 2)
    item = random.choice(ITEMS)
    initial1 = random.randint(20, 40)
    initial2 = random.randint(5, 15)
    transfer1 = random.randint(5, 15)
    transfer2 = random.randint(1, 5)

    final1 = initial1 - transfer1 + transfer2

    question = f"{name1} has {initial1} {item} and {name2} has {initial2}. {name1} gives {transfer1} to {name2}. Then {name2} gives {transfer2} back. How many does {name1} have?"

    var1 = f"{name1.lower()}.{item}"
    var2 = f"{name2.lower()}.{item}"

    return TraceExample(
        expert="entity_track",
        query=question,
        trace=[
            InitStep(var=var1, value=initial1),
            InitStep(var=var2, value=initial2),
            TransferStep(from_entity=var1, to_entity=var2, amount=transfer1),
            TransferStep(from_entity=var2, to_entity=var1, amount=transfer2),
            QueryStep(var=var1),
        ],
        answer=final1,
        expected_operation="execute_trace",
    )


def generate_find_and_lose() -> TraceExample:
    """Entity finds and loses items."""
    name = random.choice(NAMES)
    item = random.choice(ITEMS)
    initial = random.randint(10, 30)
    found = random.randint(2, 10)
    lost = random.randint(1, 5)

    final = initial + found - lost

    question = f"{name} has {initial} {item}. {name} {random.choice(FIND_VERBS)} {found} more, then {random.choice(LOSE_VERBS)} {lost}. How many does {name} have now?"

    return TraceExample(
        expert="entity_track",
        query=question,
        trace=[
            InitStep(var=item, value=initial),
            AddEntityStep(entity=item, amount=found),
            ConsumeStep(entity=item, amount=lost),
            QueryStep(var=item),
        ],
        answer=final,
        expected_operation="execute_trace",
    )


GENERATORS = [
    generate_simple_transfer,
    generate_consume_sequence,
    generate_consume_then_multiply,
    generate_bidirectional_transfer,
    generate_find_and_lose,
]


def generate(n: int = 100) -> list[TraceExample]:
    """Generate n entity tracking examples."""
    examples = []
    for _ in range(n):
        gen = random.choice(GENERATORS)
        examples.append(gen())
    return examples
