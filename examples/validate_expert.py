#!/usr/bin/env python3
"""
Generic Few-Shot Validation for Virtual Experts.

Validates that an expert works with LLM few-shot prompting before fine-tuning.

Usage:
    # Test time expert with local model
    python validate_expert.py --expert time --model mlx-community/Llama-3.2-1B-Instruct-4bit

    # Test with specific queries
    python validate_expert.py --expert time --queries "What time is it in Tokyo?" "Convert 3pm EST to PST"
"""

import argparse
import sys
from pathlib import Path

# Add packages to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "packages/chuk-virtual-expert/src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "packages/chuk-virtual-expert-time/src"))


def get_expert(expert_name: str):
    """Get expert by name."""
    if expert_name == "time":
        from chuk_virtual_expert_time import TimeExpert
        return TimeExpert()
    else:
        raise ValueError(f"Unknown expert: {expert_name}")


def get_test_data(expert_name: str) -> tuple[list[str], list]:
    """Get default test data for an expert."""
    if expert_name == "time":
        return (
            [
                "What time is it?",
                "What time is it in Tokyo?",
                "Convert 3pm EST to PST",
                "What timezone is Sydney in?",
                "Tell me a joke",  # Should NOT route to time expert
            ],
            [
                None,  # Dynamic - just check it parses
                None,  # Dynamic
                None,  # Dynamic
                None,  # Dynamic
                None,  # Should be passthrough
            ]
        )
    else:
        return [], []


def create_generate_fn(model_id: str):
    """Create generation function for a model."""
    print(f"Loading model: {model_id}")

    from mlx_lm import load, generate

    model, tokenizer = load(model_id)
    print("Model loaded!")

    def generate_fn(prompt: str, max_tokens: int = 300) -> str:
        return generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            verbose=False,
        )

    return generate_fn


def main():
    parser = argparse.ArgumentParser(
        description="Validate virtual expert with few-shot prompting"
    )
    parser.add_argument(
        "--expert",
        type=str,
        default="time",
        help="Expert to validate (default: time)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mlx-community/Llama-3.2-1B-Instruct-4bit",
        help="MLX model ID for generation",
    )
    parser.add_argument(
        "--queries",
        type=str,
        nargs="+",
        help="Custom queries to test (optional)",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=3,
        help="Number of few-shot examples",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output",
    )

    args = parser.parse_args()

    # Get expert
    print(f"\n{'='*60}")
    print(f"FEW-SHOT VALIDATION: {args.expert}")
    print(f"{'='*60}")

    expert = get_expert(args.expert)
    print(f"Expert: {expert.name}")
    print(f"Operations: {expert.get_operations()}")

    # Get test data
    if args.queries:
        queries = args.queries
        expected = [None] * len(queries)
    else:
        queries, expected = get_test_data(args.expert)

    print(f"Test queries: {len(queries)}")

    # Create generation function
    generate_fn = create_generate_fn(args.model)

    # Run validation
    from chuk_virtual_expert import validate_expert_few_shot

    summary = validate_expert_few_shot(
        expert=expert,
        generate_fn=generate_fn,
        test_queries=queries,
        expected_answers=expected,
        max_examples=args.max_examples,
        verbose=args.verbose,
    )

    # Print summary
    summary.print_summary()

    # Show sample results
    print(f"\n{'='*60}")
    print("SAMPLE RESULTS")
    print(f"{'='*60}")

    for i, result in enumerate(summary.results[:5]):
        print(f"\n[{i+1}] {result.query[:50]}...")
        print(f"    Parsed: {result.parsed}")
        print(f"    Routed: {result.routed_to_expert}")
        print(f"    Executed: {result.executed}")
        print(f"    Verified: {result.verified}")
        if result.answer is not None:
            print(f"    Answer: {result.answer}")
        if result.error:
            print(f"    Error: {result.error}")


if __name__ == "__main__":
    main()
