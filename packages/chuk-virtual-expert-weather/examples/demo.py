"""
Weather Expert Demo

Demonstrates all weather expert operations using the live MCP server.
"""

from __future__ import annotations

import asyncio
import json

from chuk_virtual_expert_weather import (
    WeatherExpert,
    WeatherOperation,
    WeatherQueryType,
)


def print_result(label: str, data: dict) -> None:
    """Pretty-print a result."""
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    print(json.dumps(data, indent=2, default=str))


async def demo_list_tools() -> None:
    """List available MCP tools from the server."""
    expert = WeatherExpert()
    print("\n=== Available MCP Tools ===")
    tools = await expert.list_mcp_tools()
    for tool in tools:
        print(f"  - {tool['name']}: {tool.get('description', '')[:60]}")


async def demo_get_forecast() -> None:
    """Get weather forecast for various locations."""
    expert = WeatherExpert()

    # Forecast with location alias
    print("\n=== Get Forecast: Tokyo ===")
    result = await expert.execute_operation_async(
        WeatherOperation.GET_FORECAST.value,
        {"location": "tokyo", "forecast_days": 1},
    )
    print_result("Tokyo Forecast", result)

    # Forecast with unit alias
    print("\n=== Get Forecast: NYC in Fahrenheit ===")
    result = await expert.execute_operation_async(
        WeatherOperation.GET_FORECAST.value,
        {"location": "nyc", "unit": "f", "forecast_days": 1},
    )
    print_result("NYC Forecast (Fahrenheit)", result)


async def demo_geocode() -> None:
    """Geocode a location name."""
    expert = WeatherExpert()
    print("\n=== Geocode: Zurich ===")
    result = await expert.execute_operation_async(
        WeatherOperation.GEOCODE.value,
        {"name": "Zurich, Switzerland"},
    )
    print_result("Geocode Result", result)


async def demo_air_quality() -> None:
    """Get air quality data."""
    expert = WeatherExpert()
    print("\n=== Air Quality: Beijing ===")
    result = await expert.execute_operation_async(
        WeatherOperation.GET_AIR_QUALITY.value,
        {"location": "beijing"},
    )
    print_result("Air Quality", result)


async def demo_marine() -> None:
    """Get marine forecast."""
    expert = WeatherExpert()
    print("\n=== Marine Forecast: Sydney ===")
    result = await expert.execute_operation_async(
        WeatherOperation.GET_MARINE.value,
        {"location": "sydney", "forecast_days": 1},
    )
    print_result("Marine Forecast", result)


async def demo_interpret_code() -> None:
    """Interpret weather codes."""
    expert = WeatherExpert()
    print("\n=== Interpret Weather Code ===")
    for code in [0, 3, 61, 95]:
        result = await expert.execute_operation_async(
            WeatherOperation.INTERPRET_CODE.value,
            {"weather_code": code},
        )
        desc = result.get("description", "unknown")
        severity = result.get("severity", "")
        print(f"  Code {code}: {desc} (severity: {severity})")


async def demo_multi_step_trace() -> None:
    """Demonstrate multi-step trace: geocode then forecast."""
    expert = WeatherExpert()
    print("\n=== Multi-Step Trace: Geocode + Forecast ===")
    result = await expert.execute_operation_async(
        "execute_trace",
        {
            "trace": [
                {"geocode": {"name": "Helsinki, Finland", "var": "loc"}},
                {"get_forecast": {"location_var": "loc", "forecast_days": 1, "var": "weather"}},
                {"query": "weather"},
            ],
        },
    )
    print_result("Multi-Step Result", result)


async def demo_can_handle() -> None:
    """Show can_handle routing examples."""
    expert = WeatherExpert()
    print("\n=== can_handle Routing ===")
    test_prompts = [
        "What's the weather in London?",
        "Will it rain tomorrow?",
        "Air quality in Beijing",
        "Ocean wave height near Miami",
        "What time is it?",
        "Calculate 2 + 2",
    ]
    for prompt in test_prompts:
        handles = expert.can_handle(prompt)
        marker = "+" if handles else "-"
        print(f"  [{marker}] {prompt}")


async def main() -> None:
    """Run all demos."""
    print("=" * 60)
    print("  Weather Expert Demo")
    print(f"  Server: https://weather.chukai.io/mcp")
    print("=" * 60)

    await demo_can_handle()
    await demo_list_tools()
    await demo_get_forecast()
    await demo_geocode()
    await demo_air_quality()
    await demo_marine()
    await demo_interpret_code()
    await demo_multi_step_trace()

    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
