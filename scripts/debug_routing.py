#!/usr/bin/env python3
"""
Debug script to understand why some queries don't route.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages/chuk-virtual-expert/src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "packages/chuk-virtual-expert-time/src"))


def main():
    try:
        import mlx.core as mx
        from mlx_lm import load
        from chuk_lazarus.inference.virtual_experts import (
            VirtualDenseWrapper,
            FewShotCoTRewriter,
        )
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return

    from chuk_virtual_expert_time import TimeExpert
    from chuk_virtual_expert.lazarus import LazarusAdapter
    import json

    # Load model
    print("Loading model...")
    model, tokenizer = load("mlx-community/Qwen2.5-0.5B-Instruct-4bit")

    # Create rewriter
    rewriter = FewShotCoTRewriter(model, tokenizer, max_examples_per_expert=10)

    # Create wrapper
    wrapper = VirtualDenseWrapper(
        model=model,
        tokenizer=tokenizer,
        model_id="Qwen2.5-0.5B",
        cot_rewriter=rewriter,
    )

    # Set up expert
    expert = TimeExpert()
    adapter = LazarusAdapter(expert)
    examples = adapter.get_cot_examples()
    rewriter.set_expert_info(
        expert_name=adapter.name,
        description=adapter.description,
        examples=examples,
    )

    wrapper.register_plugin(adapter)

    # Get calibration data
    print("\n" + "=" * 60)
    print("Calibration Data Analysis")
    print("=" * 60)

    positive, negative = adapter.get_calibration_actions()
    print(f"\nPositive actions: {len(positive)}")
    print(f"Negative actions: {len(negative)}")

    print("\nPositive action JSONs (first 3):")
    for i, action_json in enumerate(positive[:3]):
        print(f"\n  {i+1}. {action_json[:100]}...")

    # Calibrate
    print("\n" + "=" * 60)
    print("Calibrating Router")
    print("=" * 60)
    wrapper.calibrate(use_cot=True)

    # Test routing
    print("\n" + "=" * 60)
    print("Testing Routing with Action JSONs")
    print("=" * 60)

    # Test with some calibration examples
    print("\n--- Testing with calibration examples ---")
    for i, action_json in enumerate(positive[:3]):
        hidden = wrapper._get_hidden_state(action_json)
        score = wrapper.router.get_routing_score(hidden[None, None, :], 0)
        print(f"\nCalibration example {i+1}:")
        print(f"  Action: {action_json[:60]}...")
        print(f"  Score: {score:.3f}")

    # Test with live queries
    print("\n\n--- Testing with live queries ---")
    test_queries = [
        "What time is it?",
        "What time is it in Tokyo?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")

        # Get CoT action
        action = rewriter.rewrite(query, ["time"])
        action_json = action.to_json()

        print(f"  CoT Action JSON: {action_json[:80]}...")

        # Get hidden state for action JSON
        hidden = wrapper._get_hidden_state(action_json)

        # Get routing score
        score = wrapper.router.get_routing_score(hidden[None, None, :], 0)
        print(f"  Routing Score: {score:.3f}")

        # Compare with calibration example
        if query == "What time is it?":
            # Find matching calibration example
            cal_action = positive[0]  # First one is "What time is it?"
            cal_hidden = wrapper._get_hidden_state(cal_action)
            cal_score = wrapper.router.get_routing_score(cal_hidden[None, None, :], 0)
            print(f"\n  Matching calibration example:")
            print(f"    Action: {cal_action[:80]}...")
            print(f"    Score: {cal_score:.3f}")

            # Check difference
            import numpy as np
            diff = float(mx.linalg.norm(hidden - cal_hidden))
            print(f"\n  Hidden state L2 difference: {diff:.4f}")


if __name__ == "__main__":
    main()
