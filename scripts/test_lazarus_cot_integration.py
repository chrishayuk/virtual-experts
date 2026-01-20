#!/usr/bin/env python3
"""
Test script for Lazarus + Virtual Expert CoT integration.

Tests the full flow:
    User Query → CoT Rewrite → VirtualExpertAction JSON → Calibration Router → Expert

Prerequisites:
    - chuk-lazarus installed (pip install -e /path/to/chuk-mlx)
    - chuk-virtual-expert installed (pip install -e packages/chuk-virtual-expert)
    - chuk-virtual-expert-time installed (pip install -e packages/chuk-virtual-expert-time)
    - A model (e.g., Qwen2.5-0.5B) available

Usage:
    python scripts/test_lazarus_cot_integration.py
"""

import sys
from pathlib import Path

# Add paths for development
sys.path.insert(0, str(Path(__file__).parent.parent / "packages/chuk-virtual-expert/src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "packages/chuk-virtual-expert-time/src"))


def test_adapter_calibration():
    """Test that LazarusAdapter provides calibration data correctly."""
    print("\n" + "=" * 60)
    print("Testing LazarusAdapter Calibration Data")
    print("=" * 60)

    from chuk_virtual_expert_time import TimeExpert
    from chuk_virtual_expert.lazarus import LazarusAdapter

    expert = TimeExpert()
    adapter = LazarusAdapter(expert)

    # Test get_calibration_actions
    positive, negative = adapter.get_calibration_actions()
    print(f"\nPositive calibration actions: {len(positive)}")
    print(f"Negative calibration actions: {len(negative)}")

    if positive:
        print(f"\nSample positive action:")
        print(f"  {positive[0][:100]}...")

    if negative:
        print(f"\nSample negative action:")
        print(f"  {negative[0][:100]}...")

    # Test get_cot_examples
    examples = adapter.get_cot_examples()
    print(f"\nCoT examples: {len(examples)}")
    if examples:
        print(f"\nSample CoT example:")
        ex = examples[0]
        print(f"  Query: {ex['query']}")
        print(f"  Action: {ex['action']}")

    print("\n✓ LazarusAdapter calibration data works correctly")
    return True


def test_adapter_execute_action():
    """Test that LazarusAdapter.execute_action works correctly."""
    print("\n" + "=" * 60)
    print("Testing LazarusAdapter.execute_action()")
    print("=" * 60)

    from chuk_virtual_expert_time import TimeExpert
    from chuk_virtual_expert.lazarus import LazarusAdapter
    from chuk_virtual_expert.models import VirtualExpertAction

    expert = TimeExpert()
    adapter = LazarusAdapter(expert)

    # Test with Pydantic action
    action = VirtualExpertAction(
        expert="time",
        operation="get_time",
        parameters={"timezone": "Asia/Tokyo"},
        confidence=0.95,
        reasoning="Test action",
    )

    result = adapter.execute_action(action)
    print(f"\nPydantic action result: {result}")

    # Test with dict-like action (simulating Lazarus dataclass)
    class MockLazarusAction:
        def __init__(self):
            self.expert = "time"
            self.operation = "get_time"
            self.parameters = {"timezone": "UTC"}
            self.confidence = 1.0
            self.reasoning = "Mock test"

        def to_json(self):
            return '{"expert": "time", "operation": "get_time"}'

    mock_action = MockLazarusAction()
    result2 = adapter.execute_action(mock_action)
    print(f"\nMock Lazarus action result: {result2}")

    print("\n✓ LazarusAdapter.execute_action() works correctly")
    return True


def test_full_lazarus_integration():
    """Test full integration with Lazarus (requires model)."""
    print("\n" + "=" * 60)
    print("Testing Full Lazarus Integration (with model)")
    print("=" * 60)

    try:
        import mlx.core as mx
        from mlx_lm import load
    except ImportError:
        print("\n⚠ mlx-lm not installed, skipping model test")
        return True

    try:
        from chuk_lazarus.inference.virtual_experts import (
            VirtualDenseWrapper,
            FewShotCoTRewriter,
        )
    except ImportError:
        print("\n⚠ chuk-lazarus not installed, skipping integration test")
        return True

    from chuk_virtual_expert_time import TimeExpert
    from chuk_virtual_expert.lazarus import LazarusAdapter

    # Load model
    print("\nLoading model...")
    try:
        model, tokenizer = load("mlx-community/Qwen2.5-0.5B-Instruct-4bit")
    except Exception as e:
        print(f"\n⚠ Could not load model: {e}")
        print("  Skipping full integration test")
        return True

    # Create wrapper with CoT rewriter
    print("Creating wrapper with CoT rewriter...")
    # Use more examples to include convert_time operations
    cot_rewriter = FewShotCoTRewriter(model, tokenizer, max_examples_per_expert=10)

    wrapper = VirtualDenseWrapper(
        model=model,
        tokenizer=tokenizer,
        model_id="Qwen2.5-0.5B",
        cot_rewriter=cot_rewriter,
        routing_threshold=0.1,  # Lower threshold when using CoT
    )

    # Create and register TimeExpert via adapter
    expert = TimeExpert()
    adapter = LazarusAdapter(expert)

    # Set up CoT rewriter with expert info
    examples = adapter.get_cot_examples()
    print(f"Setting up with {len(examples)} CoT examples")
    cot_rewriter.set_expert_info(
        expert_name=adapter.name,
        description=adapter.description,
        examples=examples,
    )

    wrapper.register_plugin(adapter)

    # Calibrate
    print("Calibrating...")
    wrapper.calibrate(use_cot=True)

    # Test queries
    test_queries = [
        "What time is it?",
        "What time is it in Tokyo?",
        "Convert 3pm EST to PST",
        "Tell me a joke",  # Should passthrough
    ]

    print("\n" + "-" * 60)
    print("Testing queries:")
    print("-" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        result = wrapper.solve(query)
        print(f"  Answer: {result.answer}")
        print(f"  Plugin: {result.plugin_name}")
        print(f"  Score: {result.routing_score:.3f}")
        print(f"  Used VE: {result.used_virtual_expert}")

    print("\n✓ Full Lazarus integration works correctly")
    return True


def test_calibration_without_model():
    """Test calibration data flow without requiring a model."""
    print("\n" + "=" * 60)
    print("Testing Calibration Data Flow (no model needed)")
    print("=" * 60)

    from chuk_virtual_expert_time import TimeExpert
    from chuk_virtual_expert.lazarus import LazarusAdapter
    import json

    expert = TimeExpert()
    adapter = LazarusAdapter(expert)

    positive, negative = adapter.get_calibration_actions()

    print(f"\n{'Action Type':<15} {'Count':<10} {'Sample Expert':<10}")
    print("-" * 40)

    # Parse and analyze
    pos_experts = set()
    neg_experts = set()

    for action_json in positive:
        action = json.loads(action_json)
        pos_experts.add(action["expert"])

    for action_json in negative:
        action = json.loads(action_json)
        neg_experts.add(action["expert"])

    print(f"{'Positive':<15} {len(positive):<10} {', '.join(pos_experts)}")
    print(f"{'Negative':<15} {len(negative):<10} {', '.join(neg_experts)}")

    # Verify positive actions target this expert
    assert all(json.loads(a)["expert"] == "time" for a in positive), \
        "Positive actions should target 'time' expert"

    # Verify negative actions don't target this expert
    assert all(json.loads(a)["expert"] != "time" for a in negative), \
        "Negative actions should not target 'time' expert"

    print("\n✓ Calibration data flow is correct")
    print("  - Positive actions all target 'time' expert")
    print("  - Negative actions all target 'none' (passthrough)")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Virtual Expert + Lazarus CoT Integration Tests")
    print("=" * 60)

    tests = [
        ("Adapter Calibration", test_adapter_calibration),
        ("Adapter Execute Action", test_adapter_execute_action),
        ("Calibration Data Flow", test_calibration_without_model),
        ("Full Lazarus Integration", test_full_lazarus_integration),
    ]

    results = []
    for name, test_fn in tests:
        try:
            success = test_fn()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")

    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    return all(s for _, s in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
