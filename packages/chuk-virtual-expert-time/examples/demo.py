#!/usr/bin/env python3
"""
Demo script for TimeExpert backed by MCP server.

This demonstrates how the TimeExpert delegates to the hosted
MCP time server at https://time.chukai.io/mcp
"""

from __future__ import annotations

import asyncio
import json

from chuk_virtual_expert.models import VirtualExpertAction
from chuk_virtual_expert_time import TimeExpert, TimeOperation


async def demo_get_time() -> None:
    """Demo: Get current time in various timezones."""
    print("\n" + "=" * 60)
    print("Demo: Get Current Time")
    print("=" * 60)

    expert = TimeExpert()

    # Test different timezones
    timezones = ["UTC", "tokyo", "America/New_York", "london"]

    for tz in timezones:
        print(f"\n--- Time in {tz} ---")
        result = await expert.execute_operation_async(
            TimeOperation.GET_TIME.value,
            {"timezone": tz},
        )
        print(json.dumps(result, indent=2))


async def demo_convert_time() -> None:
    """Demo: Convert time between timezones."""
    print("\n" + "=" * 60)
    print("Demo: Convert Time")
    print("=" * 60)

    expert = TimeExpert()

    conversions = [
        {"time": "2024-01-15T09:00:00", "from_timezone": "nyc", "to_timezone": "tokyo"},
        {"time": "2024-06-15T14:30:00", "from_timezone": "london", "to_timezone": "pst"},
    ]

    for conv in conversions:
        print(f"\n--- {conv['time']} from {conv['from_timezone']} to {conv['to_timezone']} ---")
        result = await expert.execute_operation_async(
            TimeOperation.CONVERT_TIME.value,
            conv,
        )
        print(json.dumps(result, indent=2))


async def demo_timezone_info() -> None:
    """Demo: Get timezone information."""
    print("\n" + "=" * 60)
    print("Demo: Get Timezone Info")
    print("=" * 60)

    expert = TimeExpert()

    locations = ["tokyo", "America/Los_Angeles", "Europe/London"]

    for loc in locations:
        print(f"\n--- Timezone info for {loc} ---")
        result = await expert.execute_operation_async(
            TimeOperation.GET_TIMEZONE_INFO.value,
            {"location": loc},
        )
        print(json.dumps(result, indent=2))


async def demo_with_action() -> None:
    """Demo: Using VirtualExpertAction for full integration."""
    print("\n" + "=" * 60)
    print("Demo: Execute with VirtualExpertAction")
    print("=" * 60)

    expert = TimeExpert()

    action = VirtualExpertAction(
        expert="time",
        operation=TimeOperation.GET_TIME.value,
        parameters={"timezone": "Asia/Tokyo"},
        confidence=0.95,
        reasoning="User wants to know the current time in Tokyo",
    )

    print(f"\nAction: {action.model_dump_json(indent=2)}")

    result = await expert.execute_async(action)

    print(f"\nResult success: {result.success}")
    print(f"Result data: {json.dumps(result.data, indent=2)}")


async def demo_list_mcp_tools() -> None:
    """Demo: List available tools from MCP server."""
    print("\n" + "=" * 60)
    print("Demo: List MCP Tools")
    print("=" * 60)

    expert = TimeExpert()

    tools = await expert.list_mcp_tools()

    print(f"\nAvailable tools from {expert.mcp_server_url}:")
    for tool in tools:
        print(f"\n  - {tool['name']}")
        print(f"    {tool.get('description', 'No description')}")


async def main() -> None:
    """Run all demos."""
    print("TimeExpert MCP Demo")
    print("==================")
    print(f"Server: https://time.chukai.io/mcp")

    try:
        await demo_list_mcp_tools()
        await demo_get_time()
        await demo_convert_time()
        await demo_timezone_info()
        await demo_with_action()

        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
