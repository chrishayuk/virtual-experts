"""
CoT LLM Integration Demo.

Actually runs an LLM to rewrite queries into structured VirtualExpertActions
that guarantee plugin invocation.

Usage:
    python cot_llm_demo.py --model mlx-community/Qwen2.5-0.5B-Instruct-4bit
"""

import argparse
import json
from chuk_virtual_expert_time import TimeExpertPlugin
from chuk_virtual_expert import VirtualExpertRegistry
from chuk_virtual_expert.dispatcher import (
    VirtualExpertDispatcher,
    VirtualExpertAction,
    PromptBasedExtractor,
)


class LLMActionExtractor:
    """
    Uses an actual LLM to extract structured actions from queries.

    This implements the ActionExtractor protocol using mlx-lm.
    """

    def __init__(self, model, tokenizer, registry: VirtualExpertRegistry):
        self.model = model
        self.tokenizer = tokenizer
        self.prompt_extractor = PromptBasedExtractor(registry)
        self.registry = registry

    def extract_action(
        self,
        query: str,
        available_experts: list[str],
    ) -> VirtualExpertAction:
        """Extract a structured action using the LLM."""
        from mlx_lm import generate

        # Build the prompt
        prompt = self.prompt_extractor.get_prompt(query)

        # Generate response from LLM
        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=200,
            verbose=False,
        )

        print(f"  LLM raw response: {response[:200]}...")

        # Parse the response
        action = self.prompt_extractor.parse_response(response)
        return action


def demo_cot_extraction(model_id: str):
    """Demo the full CoT extraction pipeline."""
    print("=" * 60)
    print("COT LLM EXTRACTION DEMO")
    print("=" * 60)
    print()

    # Load model
    print(f"Loading model: {model_id}")
    try:
        from mlx_lm import load
        model, tokenizer = load(model_id)
        print("Model loaded!\n")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # Set up registry and plugin
    registry = VirtualExpertRegistry()
    plugin = TimeExpertPlugin(use_mcp=False)
    registry.register(plugin)

    # Create LLM-based extractor
    extractor = LLMActionExtractor(model, tokenizer, registry)

    # Create dispatcher with LLM extractor
    dispatcher = VirtualExpertDispatcher(registry, extractor=extractor)

    # Test queries
    test_queries = [
        "What time is it?",
        "What time is it in Tokyo?",
        "Convert 3pm EST to PST",
        "What timezone is Sydney in?",
        "Tell me a joke",  # Should not route
    ]

    print("=" * 60)
    print("TESTING QUERIES")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)

        result = dispatcher.dispatch(query)
        action = result.action

        print(f"  Extracted action:")
        print(f"    expert: {action.expert}")
        print(f"    operation: {action.operation}")
        print(f"    parameters: {action.parameters}")
        print(f"    confidence: {action.confidence}")
        print(f"    reasoning: {action.reasoning}")

        if result.result:
            print(f"  Plugin result: {result.result.data}")
        else:
            print(f"  Plugin result: [no plugin invoked]")


def main():
    parser = argparse.ArgumentParser(description="CoT LLM extraction demo")
    parser.add_argument(
        "--model",
        help="HuggingFace model ID",
        default="mlx-community/Qwen2.5-0.5B-Instruct-4bit",
    )
    args = parser.parse_args()

    demo_cot_extraction(args.model)


if __name__ == "__main__":
    main()
