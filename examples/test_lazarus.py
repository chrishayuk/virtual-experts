"""
Test virtual expert integration with Lazarus.

This script demonstrates using the time virtual expert with Lazarus's
virtual expert system.
"""

from chuk_virtual_expert_time import TimeExpertPlugin
from chuk_virtual_expert import adapt_for_lazarus

# Create and adapt the time plugin for Lazarus
time_plugin = TimeExpertPlugin(use_mcp=False)
lazarus_plugin = adapt_for_lazarus(time_plugin)

print("=== Testing Lazarus Adapter ===")
print()

# Test the adapted plugin
print(f"Plugin: {lazarus_plugin.name}")
print(f"Description: {lazarus_plugin.description}")
print(f"Priority: {lazarus_plugin.priority}")
print()

# Test queries
queries = [
    "What time is it?",
    "What time is it in Tokyo?",
    "What timezone is London in?",
]

print("=== Lazarus-Compatible Output (strings) ===")
for q in queries:
    if lazarus_plugin.can_handle(q):
        result = lazarus_plugin.execute(q)
        print(f"Q: {q}")
        print(f"A: {result}")
        print()

# Test calibration prompts
print("=== Calibration Prompts ===")
positive, negative = lazarus_plugin.get_calibration_prompts()
print(f"Positive: {len(positive)} examples")
print(f"Negative: {len(negative)} examples")
print()

# Now test with actual Lazarus
print("=== Testing with Lazarus Virtual Expert System ===")
try:
    from chuk_lazarus.inference.virtual_experts import VirtualExpertRegistry

    # Create registry and register our plugin
    registry = VirtualExpertRegistry()
    registry.register(lazarus_plugin)

    print(f"Registered plugins: {registry.plugin_names}")

    # Find handler for a query
    prompt = "What time is it in New York?"
    handler = registry.find_handler(prompt)

    if handler:
        print(f"\nQuery: {prompt}")
        print(f"Handler: {handler.name}")
        result = handler.execute(prompt)
        print(f"Result: {result}")

    print("\n✓ Lazarus integration successful!")

except ImportError as e:
    print(f"Lazarus not available: {e}")
except Exception as e:
    print(f"Error: {e}")
