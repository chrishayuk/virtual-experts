#!/usr/bin/env python3
"""
Demo script for arithmetic trace-solving virtual experts.

Demonstrates the 5 expert types and TraceVerifier integration.
All operations are async-native with typed Pydantic trace steps.
"""

from __future__ import annotations

import asyncio

import yaml
from chuk_virtual_expert import ExpertRegistry, TraceVerifier, VirtualExpertAction
from chuk_virtual_expert.trace_models import (
    ComputeOp,
    ComputeStep,
    ConsumeStep,
    FormulaStep,
    GivenStep,
    InitStep,
    PercentIncreaseStep,
    PercentOffStep,
    QueryStep,
)

from chuk_virtual_expert_arithmetic import (
    ArithmeticExpert,
    ComparisonExpert,
    EntityTrackExpert,
    PercentageExpert,
    RateEquationExpert,
)
from chuk_virtual_expert_arithmetic.generators import TraceGenerator


async def demo_entity_track() -> None:
    """Demo: Entity tracking with consume/transfer/add."""
    print("\n" + "=" * 60)
    print("Demo: Entity Tracking")
    print("=" * 60)

    expert = EntityTrackExpert()

    # Alice has 16 eggs, gives 3, eats 4, sells rest at $2 each
    steps = [
        InitStep(var="eggs", value=16),
        ConsumeStep(entity="eggs", amount=3),
        ConsumeStep(entity="eggs", amount=4),
        ComputeStep(compute_op=ComputeOp.MUL, args=["eggs", 2], var="revenue"),
        QueryStep(var="revenue"),
    ]

    result = await expert.execute_trace(steps)
    print("  Trace: 16 eggs - 3 consumed - 4 consumed, remaining * $2")
    print(f"  Answer: {result.answer} (expected: 18)")
    print(f"  State: {result.state}")
    assert result.answer == 18


async def demo_arithmetic() -> None:
    """Demo: Pure arithmetic chains."""
    print("\n" + "=" * 60)
    print("Demo: Arithmetic")
    print("=" * 60)

    expert = ArithmeticExpert()

    # 2 books at $15 + 4 pens at $3
    steps = [
        InitStep(var="book_price", value=15),
        InitStep(var="pen_price", value=3),
        ComputeStep(compute_op=ComputeOp.MUL, args=["book_price", 2], var="books_total"),
        ComputeStep(compute_op=ComputeOp.MUL, args=["pen_price", 4], var="pens_total"),
        ComputeStep(compute_op=ComputeOp.ADD, args=["books_total", "pens_total"], var="total"),
        QueryStep(var="total"),
    ]

    result = await expert.execute_trace(steps)
    print("  Trace: 2 * $15 + 4 * $3")
    print(f"  Answer: {result.answer} (expected: 42)")
    assert result.answer == 42


async def demo_percentage() -> None:
    """Demo: Percentage calculations."""
    print("\n" + "=" * 60)
    print("Demo: Percentage")
    print("=" * 60)

    expert = PercentageExpert()

    # $200 jacket, 25% off
    steps = [
        InitStep(var="price", value=200),
        PercentOffStep(base="price", rate=25, var="sale_price"),
        QueryStep(var="sale_price"),
    ]

    result = await expert.execute_trace(steps)
    print("  Trace: $200 - 25% off")
    print(f"  Answer: {result.answer} (expected: 150)")
    assert result.answer == 150

    # $1500 rent, 10% increase
    steps2 = [
        InitStep(var="rent", value=1500),
        PercentIncreaseStep(base="rent", rate=10, var="new_rent"),
        QueryStep(var="new_rent"),
    ]

    result2 = await expert.execute_trace(steps2)
    print("  Trace: $1500 + 10% increase")
    print(f"  Answer: {result2.answer} (expected: 1650)")
    assert abs(result2.answer - 1650) < 0.01


async def demo_rate_equation() -> None:
    """Demo: Rate/formula problems."""
    print("\n" + "=" * 60)
    print("Demo: Rate Equation")
    print("=" * 60)

    expert = RateEquationExpert()

    # 60 km/h for 2.5 hours
    steps = [
        GivenStep(values={"speed": 60, "time": 2.5}),
        FormulaStep(expression="distance = speed * time"),
        ComputeStep(compute_op=ComputeOp.MUL, args=["speed", "time"], var="distance"),
        QueryStep(var="distance"),
    ]

    result = await expert.execute_trace(steps)
    print("  Trace: 60 km/h * 2.5 hours")
    print(f"  Answer: {result.answer} (expected: 150)")
    assert result.answer == 150


async def demo_comparison() -> None:
    """Demo: Comparison calculations."""
    print("\n" + "=" * 60)
    print("Demo: Comparison")
    print("=" * 60)

    expert = ComparisonExpert()

    # Tom has 3x Jerry's books, Jerry has 12. Difference?
    steps = [
        InitStep(var="jerry_books", value=12),
        ComputeStep(compute_op=ComputeOp.MUL, args=["jerry_books", 3], var="tom_books"),
        ComputeStep(compute_op=ComputeOp.SUB, args=["tom_books", "jerry_books"], var="difference"),
        QueryStep(var="difference"),
    ]

    result = await expert.execute_trace(steps)
    print("  Trace: Tom=3*12, difference=Tom-Jerry")
    print(f"  Answer: {result.answer} (expected: 24)")
    assert result.answer == 24


async def demo_verifier() -> None:
    """Demo: TraceVerifier with graduated rewards."""
    print("\n" + "=" * 60)
    print("Demo: TraceVerifier (Graduated Rewards)")
    print("=" * 60)

    registry = ExpertRegistry()
    registry.register(EntityTrackExpert())
    registry.register(ArithmeticExpert())
    registry.register(PercentageExpert())
    registry.register(RateEquationExpert())
    registry.register(ComparisonExpert())
    verifier = TraceVerifier(registry)

    # Correct answer (new typed trace format)
    yaml_correct = """
expert: entity_track
trace:
  - {op: init, var: eggs, value: 16}
  - {op: consume, entity: eggs, amount: 3}
  - {op: consume, entity: eggs, amount: 4}
  - {op: compute, compute_op: mul, args: [eggs, 2], var: revenue}
  - {op: query, var: revenue}
"""
    result = await verifier.verify(yaml_correct, expected_answer=18)
    print(f"  Correct answer:   reward={result.reward} (expected 1.0)")
    assert result.reward == 1.0

    # Wrong answer
    result2 = await verifier.verify(yaml_correct, expected_answer=99)
    print(f"  Wrong answer:     reward={result2.reward} (expected 0.7)")
    assert result2.reward == 0.7

    # Invalid trace (consume from non-existent entity)
    yaml_bad = "expert: entity_track\ntrace:\n  - {op: consume, entity: missing, amount: 99}\n"
    result3 = await verifier.verify(yaml_bad, expected_answer=10)
    print(f"  Invalid trace:    reward={result3.reward} (expected 0.5)")
    assert result3.reward == 0.5

    # Bad YAML
    result4 = await verifier.verify("{{{{not yaml", expected_answer=10)
    print(f"  Bad YAML:         reward={result4.reward} (expected 0.0)")
    assert result4.reward == 0.0


async def demo_virtual_expert_action() -> None:
    """Demo: Using VirtualExpertAction for dispatch."""
    print("\n" + "=" * 60)
    print("Demo: VirtualExpertAction Dispatch")
    print("=" * 60)

    expert = EntityTrackExpert()

    action = VirtualExpertAction(
        expert="entity_track",
        operation="execute_trace",
        parameters={
            "trace": [
                {"op": "init", "var": "items", "value": 50},
                {"op": "consume", "entity": "items", "amount": 12},
                {"op": "consume", "entity": "items", "amount": 8},
                {"op": "query", "var": "items"},
            ]
        },
        confidence=0.95,
        reasoning="Entity tracking problem with consumption",
    )

    result = await expert.execute(action)
    print(f"  Action expert: {action.expert}")
    print(f"  Result success: {result.success}")
    print(f"  Answer: {result.data['answer']} (expected: 30)")
    assert result.data["answer"] == 30


async def demo_generator() -> None:
    """Demo: TraceGenerator for synthetic training data."""
    print("\n" + "=" * 60)
    print("Demo: TraceGenerator")
    print("=" * 60)

    gen = TraceGenerator(seed=42)
    examples = gen.generate_all(n_per_type=2)
    print(f"  Generated {len(examples)} examples across 5 expert types")

    # Verify all generated examples
    registry = ExpertRegistry()
    registry.register(EntityTrackExpert())
    registry.register(ArithmeticExpert())
    registry.register(PercentageExpert())
    registry.register(RateEquationExpert())
    registry.register(ComparisonExpert())
    verifier = TraceVerifier(registry)

    correct = 0
    for ex in examples:
        yaml_str = yaml.dump(
            {"expert": ex.expert, "trace": [s.model_dump(mode="json") for s in ex.trace]}
        )
        result = await verifier.verify(yaml_str, expected_answer=ex.answer)
        if result.answer_correct:
            correct += 1

    print(f"  Verified: {correct}/{len(examples)} correct")
    assert correct == len(examples)


async def main() -> None:
    """Run all demos."""
    print("Arithmetic Trace Experts Demo")
    print("=" * 60)

    await demo_entity_track()
    await demo_arithmetic()
    await demo_percentage()
    await demo_rate_equation()
    await demo_comparison()
    await demo_verifier()
    await demo_virtual_expert_action()
    await demo_generator()

    print("\n" + "=" * 60)
    print("All demos passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
