"""
Demo: CoT-based dispatch for virtual experts.

Shows how chain-of-thought reasoning can normalize queries into
structured actions that guarantee plugin invocation.

This approach:
1. Eliminates fuzzy pattern matching
2. Extracts parameters reliably
3. Works consistently regardless of query phrasing
"""

from chuk_virtual_expert_time import TimeExpertPlugin
from chuk_virtual_expert import VirtualExpertRegistry
from chuk_virtual_expert.dispatcher import (
    VirtualExpertDispatcher,
    VirtualExpertAction,
    PromptBasedExtractor,
)


def demo_structured_operations():
    """Show direct structured operation calls."""
    print("=" * 60)
    print("STRUCTURED OPERATIONS (CoT would produce these)")
    print("=" * 60)
    print()

    plugin = TimeExpertPlugin(use_mcp=False)

    # These are the structured calls that CoT would produce
    operations = [
        ("get_time", {"timezone": "UTC"}),
        ("get_time", {"timezone": "Asia/Tokyo"}),
        ("get_time", {"timezone": "new york"}),  # Alias works too
        ("convert_time", {"time": "3pm", "from_timezone": "EST", "to_timezone": "PST"}),
        ("get_timezone_info", {"location": "sydney"}),
    ]

    for op_name, params in operations:
        print(f"Operation: {op_name}")
        print(f"Parameters: {params}")

        # Call the operation directly
        method = getattr(plugin, op_name)
        result = method(**params)

        print(f"Result: {result}")
        print()


def demo_dispatcher():
    """Show the dispatcher in action."""
    print("=" * 60)
    print("DISPATCHER (simulated CoT extraction)")
    print("=" * 60)
    print()

    # Set up registry and dispatcher
    registry = VirtualExpertRegistry()
    plugin = TimeExpertPlugin(use_mcp=False)
    registry.register(plugin)

    dispatcher = VirtualExpertDispatcher(registry)

    # Simulate what CoT would extract from natural language
    simulated_extractions = [
        # (natural query, what CoT would extract)
        (
            "What time is it?",
            VirtualExpertAction(
                expert="time",
                operation="get_time",
                parameters={"timezone": "UTC"},
                reasoning="User wants current time, no timezone specified → UTC",
            )
        ),
        (
            "What time is it in Tokyo?",
            VirtualExpertAction(
                expert="time",
                operation="get_time",
                parameters={"timezone": "Asia/Tokyo"},
                reasoning="User wants time in Tokyo → Asia/Tokyo timezone",
            )
        ),
        (
            "What's 3pm Eastern in Pacific time?",
            VirtualExpertAction(
                expert="time",
                operation="convert_time",
                parameters={
                    "time": "3pm",
                    "from_timezone": "America/New_York",
                    "to_timezone": "America/Los_Angeles",
                },
                reasoning="Converting time between US timezones",
            )
        ),
        (
            "What timezone is Dubai in?",
            VirtualExpertAction(
                expert="time",
                operation="get_timezone_info",
                parameters={"location": "dubai"},
                reasoning="User asking about timezone, not current time",
            )
        ),
        (
            "Tell me a joke",  # Not time-related
            VirtualExpertAction(
                expert="none",
                operation="passthrough",
                parameters={},
                reasoning="Not a time-related query",
            )
        ),
    ]

    for query, action in simulated_extractions:
        print(f"Query: {query}")
        print(f"CoT extracted: {action.expert}.{action.operation}({action.parameters})")
        print(f"Reasoning: {action.reasoning}")

        # Execute if it's a real action
        if action.expert != "none":
            method = getattr(plugin, action.operation)
            result = method(**action.parameters)
            print(f"Result: {result}")
        else:
            print("Result: [passthrough to model]")
        print()


def demo_prompt_template():
    """Show the prompt template for LLM-based extraction."""
    print("=" * 60)
    print("PROMPT TEMPLATE (for LLM extraction)")
    print("=" * 60)
    print()

    registry = VirtualExpertRegistry()
    plugin = TimeExpertPlugin(use_mcp=False)
    registry.register(plugin)

    extractor = PromptBasedExtractor(registry)
    prompt = extractor.get_prompt("What time is it in Tokyo?")

    print(prompt)
    print()

    print("Expected LLM response:")
    print("""
{
    "expert": "time",
    "operation": "get_time",
    "parameters": {"timezone": "Asia/Tokyo"},
    "confidence": 0.95,
    "reasoning": "User asking for current time in Tokyo"
}
""")


def main():
    demo_structured_operations()
    print("\n")
    demo_dispatcher()
    print("\n")
    demo_prompt_template()


if __name__ == "__main__":
    main()
