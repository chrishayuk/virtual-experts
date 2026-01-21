"""
Lazarus Integration Example for Virtual Experts.

This example shows how to use virtual expert plugins with Lazarus's
MoE routing system.

Usage:
    # Basic registry test (no model needed)
    python lazarus_integration.py

    # Full test with model (requires downloaded model)
    python lazarus_integration.py --model mlx-community/Qwen2.5-0.5B-Instruct-4bit
"""

import argparse
from chuk_virtual_expert_time import TimeExpert
from chuk_virtual_expert import adapt_expert


def test_registry():
    """Test plugin registration with Lazarus registry."""
    from chuk_lazarus.inference.virtual_experts import VirtualExpertRegistry

    print("=== Registry Integration Test ===\n")

    # Create and adapt the time expert
    time_expert = TimeExpert()
    lazarus_plugin = adapt_expert(time_expert)

    # Register with Lazarus
    registry = VirtualExpertRegistry()
    registry.register(lazarus_plugin)

    print(f"Registered plugins: {registry.plugin_names}")
    print(f"All plugins: {registry.get_all()}")
    print()

    # Test finding handlers
    test_prompts = [
        ("What time is it in Tokyo?", True),
        ("What is 2 + 2?", False),
        ("Current UTC time", True),
        ("Write a poem", False),
    ]

    print("Handler lookup tests:")
    for prompt, should_handle in test_prompts:
        handler = registry.find_handler(prompt)
        found = handler is not None
        status = "✓" if found == should_handle else "✗"
        print(f"  {status} '{prompt[:40]}...' -> {handler.name if handler else 'None'}")

    print("\n✓ Registry integration successful!")


def test_with_model(model_id: str):
    """Test full integration with a model."""
    from chuk_lazarus.inference.virtual_experts import VirtualMoEWrapper
    from chuk_lazarus.inference.virtual_experts.dense_wrapper import VirtualDenseWrapper
    from chuk_lazarus.inference.virtual_experts import VirtualExpertRegistry

    print(f"\n=== Full Model Integration Test ===")
    print(f"Model: {model_id}\n")

    # Load model
    print("Loading model...")
    try:
        import mlx.core as mx
        from mlx_lm import load

        model, tokenizer = load(model_id)
        print(f"Model loaded: {type(model).__name__}")
    except Exception as e:
        print(f"Failed to load model: {e}")
        print("Try: pip install mlx-lm")
        return

    # Create registry and register our expert first
    registry = VirtualExpertRegistry()
    time_expert = TimeExpert()
    lazarus_plugin = adapt_expert(time_expert)
    registry.register(lazarus_plugin)

    # Create wrapper - try MoE first, fall back to Dense
    print("Creating virtual expert wrapper...")
    wrapper = None
    try:
        wrapper = VirtualMoEWrapper(model, tokenizer, model_id=model_id, registry=registry)
        print("Using VirtualMoEWrapper (MoE model)")
    except Exception as e:
        print(f"MoE wrapper failed: {e}")
        print("Trying VirtualDenseWrapper for dense model...")
        try:
            wrapper = VirtualDenseWrapper(
                model, tokenizer,
                model_id=model_id,
                registry=registry,
                routing_threshold=0.2  # Lower threshold for testing
            )
            print("Using VirtualDenseWrapper (dense model)")
        except Exception as e2:
            print(f"Dense wrapper also failed: {e2}")
            import traceback
            traceback.print_exc()
            return

    print(f"Registered plugins: {[p.name for p in wrapper.registry.get_all()]}")

    # Calibrate
    print("\nCalibrating router...")
    try:
        wrapper.calibrate()
        print("Calibration complete!")
    except Exception as e:
        print(f"Calibration failed: {e}")
        return

    # Test queries
    print("\n=== Test Queries ===")
    test_prompts = [
        "What time is it?",
        "What time is it in Tokyo?",
        "127 * 89 = ",  # Math (should use math expert if available)
    ]

    for prompt in test_prompts:
        print(f"\nQ: {prompt}")
        try:
            result = wrapper.solve(prompt)
            print(f"A: {result.answer[:100] if result.answer else 'None'}")
            print(f"   Used virtual expert: {result.used_virtual_expert}")
            if result.plugin_name:
                print(f"   Plugin: {result.plugin_name}")
            # Show routing score even if not routed
            if hasattr(result, 'routing_score'):
                print(f"   Routing score: {result.routing_score:.3f}" if result.routing_score else "   Routing score: None")
            if hasattr(result, 'routing_scores') and result.routing_scores:
                print(f"   All scores: {result.routing_scores}")
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n✓ Full integration test complete!")


def main():
    parser = argparse.ArgumentParser(description="Test Lazarus integration")
    parser.add_argument(
        "--model",
        help="HuggingFace model ID for full test",
        default=None,
    )
    args = parser.parse_args()

    # Always run registry test
    test_registry()

    # Run model test if specified
    if args.model:
        test_with_model(args.model)
    else:
        print("\nTo test with a model, run:")
        print("  python lazarus_integration.py --model mlx-community/Qwen2.5-0.5B-Instruct-4bit")


if __name__ == "__main__":
    main()
