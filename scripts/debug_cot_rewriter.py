#!/usr/bin/env python3
"""
Debug script to see what the CoT rewriter produces.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "packages/chuk-virtual-expert/src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "packages/chuk-virtual-expert-time/src"))


def main():
    try:
        import mlx.core as mx
        from mlx_lm import load
        from chuk_lazarus.inference.virtual_experts import FewShotCoTRewriter
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return

    from chuk_virtual_expert_time import TimeExpert
    from chuk_virtual_expert.lazarus import LazarusAdapter

    # Load model
    print("Loading model...")
    model, tokenizer = load("mlx-community/Qwen2.5-0.5B-Instruct-4bit")

    # Create rewriter
    rewriter = FewShotCoTRewriter(model, tokenizer, max_examples_per_expert=5)

    # Set up expert info
    expert = TimeExpert()
    adapter = LazarusAdapter(expert)
    examples = adapter.get_cot_examples()

    print(f"\nSetting up rewriter with {len(examples)} examples:")
    for i, ex in enumerate(examples[:3]):
        print(f"  {i+1}. Query: {ex['query']}")
        print(f"      Action: {ex['action']}")

    rewriter.set_expert_info(
        expert_name=adapter.name,
        description=adapter.description,
        examples=examples,
    )

    # Test queries
    test_queries = [
        "What time is it?",
        "What time is it in Tokyo?",
        "Convert 3pm EST to PST",
        "Tell me a joke",
    ]

    print("\n" + "=" * 60)
    print("Testing CoT Rewriter Output")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)

        # Build and show the prompt
        prompt = rewriter._build_prompt(query, ["time"])
        print(f"Prompt (last 500 chars):")
        print(prompt[-500:])
        print()

        # Rewrite
        action = rewriter.rewrite(query, ["time"])
        print(f"Result:")
        print(f"  Expert: {action.expert}")
        print(f"  Operation: {action.operation}")
        print(f"  Parameters: {action.parameters}")
        print(f"  Confidence: {action.confidence}")
        print(f"  Reasoning: {action.reasoning}")


if __name__ == "__main__":
    main()
