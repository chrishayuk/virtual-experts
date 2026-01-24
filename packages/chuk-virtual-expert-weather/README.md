# chuk-virtual-expert-weather

Weather virtual expert backed by MCP server - forecasts, air quality, and marine weather for LLM routing.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

A virtual expert plugin that provides weather data via the hosted MCP server at `https://weather.chukai.io/mcp`. Powered by Open-Meteo for global weather, air quality, and marine forecast data.

**Features:**
- **Weather forecasts** - Current conditions and multi-day forecasts
- **Air quality** - AQI, PM2.5, PM10, and pollutant data
- **Marine forecasts** - Wave height, ocean temperature, currents
- **Historical weather** - Data from 1940+ for any location
- **Geocoding** - Convert location names to coordinates
- **WMO code interpretation** - Decode weather condition codes
- **30+ location aliases** - Common cities resolved automatically
- **Async-native** - Built for async/await patterns
- **Pydantic-native** - Type-safe with structured responses
- **No magic strings** - Uses enums throughout

## Installation

```bash
pip install chuk-virtual-expert-weather
```

For development:
```bash
pip install chuk-virtual-expert-weather[dev]
```

## Quick Start

### Using execute_operation_async

```python
import asyncio
from chuk_virtual_expert_weather import WeatherExpert, WeatherOperation

expert = WeatherExpert()

async def main():
    # Get forecast for Tokyo
    result = await expert.execute_operation_async(
        WeatherOperation.GET_FORECAST.value,
        {"location": "tokyo", "forecast_days": 3}
    )
    print(result)
    # {'query_type': 'forecast', 'location': 'tokyo', 'latitude': 35.6762, ...}

    # Get air quality in Beijing
    result = await expert.execute_operation_async(
        WeatherOperation.GET_AIR_QUALITY.value,
        {"location": "beijing"}
    )
    print(result)

    # Get marine forecast for Sydney
    result = await expert.execute_operation_async(
        WeatherOperation.GET_MARINE.value,
        {"location": "sydney", "forecast_days": 5}
    )
    print(result)

asyncio.run(main())
```

### Using VirtualExpertAction

```python
import asyncio
from chuk_virtual_expert_weather import WeatherExpert, WeatherOperation
from chuk_virtual_expert.models import VirtualExpertAction

expert = WeatherExpert()

action = VirtualExpertAction(
    expert="weather",
    operation=WeatherOperation.GET_FORECAST.value,
    parameters={"location": "london", "unit": "celsius"},
)
result = asyncio.run(expert.execute_async(action))

print(result.success)  # True
print(result.data)     # {'query_type': 'forecast', ...}
```

### Multi-step Trace (Geocode + Forecast)

```python
import asyncio
from chuk_virtual_expert_weather import WeatherExpert

expert = WeatherExpert()

async def main():
    # Chain geocode -> forecast for unknown locations
    result = await expert.execute_operation_async(
        "execute_trace",
        {"trace": [
            {"geocode": {"name": "Springfield, IL", "result_var": "loc"}},
            {"get_forecast": {"location_var": "loc", "forecast_days": 3, "result_var": "weather"}},
            {"query": "weather"}
        ]}
    )
    print(result)

asyncio.run(main())
```

## Operations

### get_forecast

Get current weather and forecast for a location.

**Parameters:**
- `location`: City alias or lat/lon coordinates
- `forecast_days` (optional): Number of forecast days (1-16, default: 3)
- `unit` (optional): Temperature unit ("celsius" or "fahrenheit")

### geocode

Convert a location name to coordinates.

**Parameters:**
- `name`: Location name to search
- `count` (optional): Maximum results to return (default: 5)

### get_historical

Get historical weather data.

**Parameters:**
- `location`: City alias or lat/lon coordinates
- `start_date`: Start date (YYYY-MM-DD format)
- `end_date`: End date (YYYY-MM-DD format)

### get_air_quality

Get air quality data for a location.

**Parameters:**
- `location`: City alias or lat/lon coordinates
- `forecast_days` (optional): Number of forecast days

### get_marine

Get marine/ocean weather forecast.

**Parameters:**
- `location`: City alias or lat/lon coordinates
- `forecast_days` (optional): Number of forecast days

### interpret_code

Interpret a WMO weather code number.

**Parameters:**
- `weather_code`: Integer WMO weather code

## Enums

### WeatherOperation

```python
from chuk_virtual_expert_weather import WeatherOperation

WeatherOperation.GET_FORECAST     # "get_forecast"
WeatherOperation.GEOCODE          # "geocode"
WeatherOperation.GET_HISTORICAL   # "get_historical"
WeatherOperation.GET_AIR_QUALITY  # "get_air_quality"
WeatherOperation.GET_MARINE       # "get_marine"
WeatherOperation.INTERPRET_CODE   # "interpret_code"
```

### WeatherMCPTool

MCP tool names on the server:

```python
from chuk_virtual_expert_weather import WeatherMCPTool

WeatherMCPTool.GET_WEATHER_FORECAST    # "get_weather_forecast"
WeatherMCPTool.GEOCODE_LOCATION        # "geocode_location"
WeatherMCPTool.GET_HISTORICAL_WEATHER  # "get_historical_weather"
WeatherMCPTool.GET_AIR_QUALITY         # "get_air_quality"
WeatherMCPTool.GET_MARINE_FORECAST     # "get_marine_forecast"
WeatherMCPTool.INTERPRET_WEATHER_CODE  # "interpret_weather_code"
```

### WeatherQueryType

```python
from chuk_virtual_expert_weather import WeatherQueryType

WeatherQueryType.FORECAST      # "forecast"
WeatherQueryType.GEOCODE       # "geocode"
WeatherQueryType.HISTORICAL    # "historical"
WeatherQueryType.AIR_QUALITY   # "air_quality"
WeatherQueryType.MARINE        # "marine"
WeatherQueryType.WEATHER_CODE  # "weather_code"
WeatherQueryType.ERROR         # "error"
```

### Unit Enums

```python
from chuk_virtual_expert_weather import TemperatureUnit, WindSpeedUnit, PrecipitationUnit

TemperatureUnit.CELSIUS       # "celsius"
TemperatureUnit.FAHRENHEIT    # "fahrenheit"

WindSpeedUnit.KMH   # "kmh"
WindSpeedUnit.MS    # "ms"
WindSpeedUnit.MPH   # "mph"
WindSpeedUnit.KN    # "kn"

PrecipitationUnit.MM    # "mm"
PrecipitationUnit.INCH  # "inch"
```

## Location Aliases

Common city names are resolved automatically to lat/lon coordinates:

| Alias | Coordinates |
|-------|-------------|
| tokyo | 35.68N, 139.65E |
| london | 51.51N, 0.13W |
| new york, nyc | 40.71N, 74.01W |
| la, los angeles | 34.05N, 118.24W |
| paris | 48.86N, 2.35E |
| sydney | 33.87S, 151.21E |
| berlin | 52.52N, 13.41E |
| moscow | 55.76N, 37.62E |
| beijing | 39.90N, 116.41E |
| singapore | 1.35N, 103.82E |
| dubai | 25.20N, 55.27E |
| mumbai | 19.08N, 72.88E |
| sf, san francisco | 37.77N, 122.42W |
| chicago | 41.88N, 87.63W |
| miami | 25.76N, 80.19W |

Unknown locations can be geocoded first using the `geocode` operation.

## API Reference

### WeatherExpert

Main expert class for weather operations.

**Class Attributes:**
- `name = "weather"` - Expert identifier
- `description` - Human-readable description
- `version = "1.0.0"` - Expert version
- `priority = 5` - Routing priority
- `mcp_server_url = "https://weather.chukai.io/mcp"` - MCP server endpoint
- `mcp_timeout = 30.0` - Request timeout in seconds

**Methods:**
- `get_operations() -> list[str]` - Returns available operations
- `execute_operation_async(operation, parameters) -> dict` - Execute asynchronously
- `execute_async(action) -> VirtualExpertResult` - Execute action asynchronously
- `can_handle(prompt) -> bool` - Check if prompt is weather-related
- `list_mcp_tools() -> list[dict]` - List available MCP tools

## Development

```bash
# Clone and install
git clone https://github.com/chrishayuk/virtual-experts
cd virtual-experts/packages/chuk-virtual-expert-weather
make dev-install

# Run tests
make test

# Run tests with coverage
make test-cov

# Run all checks (lint, format, mypy, bandit, tests)
make check

# Format code
make format

# Build package
make build
```

## Dependencies

- **chuk-virtual-expert[mcp]** - Base virtual expert with MCP support
- **chuk-mcp** - MCP client library

## License

MIT License - see [LICENSE](LICENSE) for details.
