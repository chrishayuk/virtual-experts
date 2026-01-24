#!/usr/bin/env python3
"""
Demo script for arithmetic trace-solving virtual experts.

Demonstrates the 5 expert types and TraceVerifier integration.
"""

from __future__ import annotations

from chuk_virtual_expert import ExpertRegistry, TraceVerifier, VirtualExpertAction
from chuk_virtual_expert_arithmetic import (
    ArithmeticExpert,
    ComparisonExpert,
    EntityTrackExpert,
    PercentageExpert,
    RateEquationExpert,
)
from chuk_virtual_expert_arithmetic.generators import TraceGenerator


def demo_entity_track() -> None:
    """Demo: Entity tracking with consume/transfer/add."""
    print("\n" + "=" * 60)
    print("Demo: Entity Tracking")
    print("=" * 60)

    expert = EntityTrackExpert()

    # Alice has 16 eggs, gives 3, eats 4, sells rest at $2 each
    trace = [
        {"init": "eggs", "value": 16},
        {"consume": {"entity": "eggs", "amount": 3}},
        {"consume": {"entity": "eggs", "amount": 4}},
        {"compute": {"op": "mul", "args": ["eggs", 2], "var": "revenue"}},
        {"query": "revenue"},
    ]

    result = expert.execute_trace(trace)
    print(f"  Trace: 16 eggs - 3 consumed - 4 consumed, remaining * $2")
    print(f"  Answer: {result.answer} (expected: 18)")
    print(f"  State: {result.state}")
    assert result.answer == 18


def demo_arithmetic() -> None:
    """Demo: Pure arithmetic chains."""
    print("\n" + "=" * 60)
    print("Demo: Arithmetic")
    print("=" * 60)

    expert = ArithmeticExpert()

    # 2 books at $15 + 4 pens at $3
    trace = [
        {"init": "book_price", "value": 15},
        {"init": "pen_price", "value": 3},
        {"compute": {"op": "mul", "args": ["book_price", 2], "var": "books_total"}},
        {"compute": {"op": "mul", "args": ["pen_price", 4], "var": "pens_total"}},
        {"compute": {"op": "add", "args": ["books_total", "pens_total"], "var": "total"}},
        {"query": "total"},
    ]

    result = expert.execute_trace(trace)
    print(f"  Trace: 2 * $15 + 4 * $3")
    print(f"  Answer: {result.answer} (expected: 42)")
    assert result.answer == 42


def demo_percentage() -> None:
    """Demo: Percentage calculations."""
    print("\n" + "=" * 60)
    print("Demo: Percentage")
    print("=" * 60)

    expert = PercentageExpert()

    # $200 jacket, 25% off
    trace = [
        {"init": "price", "value": 200},
        {"percent_off": {"base": "price", "rate": 25, "var": "sale_price"}},
        {"query": "sale_price"},
    ]

    result = expert.execute_trace(trace)
    print(f"  Trace: $200 - 25% off")
    print(f"  Answer: {result.answer} (expected: 150)")
    assert result.answer == 150

    # $1500 rent, 10% increase
    trace2 = [
        {"init": "rent", "value": 1500},
        {"percent_increase": {"base": "rent", "rate": 10, "var": "new_rent"}},
        {"query": "new_rent"},
    ]

    result2 = expert.execute_trace(trace2)
    print(f"  Trace: $1500 + 10% increase")
    print(f"  Answer: {result2.answer} (expected: 1650)")
    assert abs(result2.answer - 1650) < 0.01


def demo_rate_equation() -> None:
    """Demo: Rate/formula problems."""
    print("\n" + "=" * 60)
    print("Demo: Rate Equation")
    print("=" * 60)

    expert = RateEquationExpert()

    # 60 km/h for 2.5 hours
    trace = [
        {"given": {"speed": 60, "time": 2.5}},
        {"formula": "distance = speed * time"},
        {"compute": {"op": "mul", "args": ["speed", "time"], "var": "distance"}},
        {"query": "distance"},
    ]

    result = expert.execute_trace(trace)
    print(f"  Trace: 60 km/h * 2.5 hours")
    print(f"  Answer: {result.answer} (expected: 150)")
    assert result.answer == 150


def demo_comparison() -> None:
    """Demo: Comparison calculations."""
    print("\n" + "=" * 60)
    print("Demo: Comparison")
    print("=" * 60)

    expert = ComparisonExpert()

    # Tom has 3x Jerry's books, Jerry has 12. Difference?
    trace = [
        {"init": "jerry_books", "value": 12},
        {"compute": {"op": "mul", "args": ["jerry_books", 3], "var": "tom_books"}},
        {"compare": {"op": "sub", "args": ["tom_books", "jerry_books"], "var": "difference"}},
        {"query": "difference"},
    ]

    result = expert.execute_trace(trace)
    print(f"  Trace: Tom=3*12, difference=Tom-Jerry")
    print(f"  Answer: {result.answer} (expected: 24)")
    assert result.answer == 24


def demo_verifier() -> None:
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

    # Correct answer
    yaml_correct = """
expert: entity_track
trace:
  - {init: eggs, value: 16}
  - {consume: {entity: eggs, amount: 3}}
  - {consume: {entity: eggs, amount: 4}}
  - {compute: {op: mul, args: [eggs, 2], var: revenue}}
  - {query: revenue}
"""
    result = verifier.verify(yaml_correct, expected_answer=18)
    print(f"  Correct answer:   reward={result.reward} (expected 1.0)")
    assert result.reward == 1.0

    # Wrong answer
    result2 = verifier.verify(yaml_correct, expected_answer=99)
    print(f"  Wrong answer:     reward={result2.reward} (expected 0.7)")
    assert result2.reward == 0.7

    # Invalid trace
    yaml_bad = "expert: entity_track\ntrace:\n  - {consume: {entity: missing, amount: 99}}\n"
    result3 = verifier.verify(yaml_bad, expected_answer=10)
    print(f"  Invalid trace:    reward={result3.reward} (expected 0.5)")
    assert result3.reward == 0.5

    # Bad YAML
    result4 = verifier.verify("{{{{not yaml", expected_answer=10)
    print(f"  Bad YAML:         reward={result4.reward} (expected 0.0)")
    assert result4.reward == 0.0


def demo_virtual_expert_action() -> None:
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
                {"init": "items", "value": 50},
                {"consume": {"entity": "items", "amount": 12}},
                {"consume": {"entity": "items", "amount": 8}},
                {"query": "items"},
            ]
        },
        confidence=0.95,
        reasoning="Entity tracking problem with consumption",
    )

    result = expert.execute(action)
    print(f"  Action expert: {action.expert}")
    print(f"  Result success: {result.success}")
    print(f"  Answer: {result.data['answer']} (expected: 30)")
    assert result.data["answer"] == 30


def demo_generator() -> None:
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

    import yaml
    correct = 0
    for ex in examples:
        yaml_str = yaml.dump({"expert": ex["expert"], "trace": ex["trace"]})
        result = verifier.verify(yaml_str, expected_answer=ex["expected_answer"])
        if result.answer_correct:
            correct += 1

    print(f"  Verified: {correct}/{len(examples)} correct")
    assert correct == len(examples)


def main() -> None:
    """Run all demos."""
    print("Arithmetic Trace Experts Demo")
    print("=" * 60)

    demo_entity_track()
    demo_arithmetic()
    demo_percentage()
    demo_rate_equation()
    demo_comparison()
    demo_verifier()
    demo_virtual_expert_action()
    demo_generator()

    print("\n" + "=" * 60)
    print("All demos passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
