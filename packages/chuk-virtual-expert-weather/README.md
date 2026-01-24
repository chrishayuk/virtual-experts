# chuk-virtual-expert-weather

Weather virtual expert backed by the Open-Meteo MCP server.

Provides weather forecasts, air quality, marine conditions, and historical weather data via `https://weather.chukai.io/mcp`.

## Operations

| Operation | MCP Tool | Description |
|-----------|----------|-------------|
| `get_forecast` | `get_weather_forecast` | Current conditions and forecast |
| `geocode` | `geocode_location` | Convert location name to coordinates |
| `get_historical` | `get_historical_weather` | Historical data from 1940+ |
| `get_air_quality` | `get_air_quality` | Air quality and pollutant data |
| `get_marine` | `get_marine_forecast` | Ocean/marine weather |
| `interpret_code` | `interpret_weather_code` | WMO code interpretation |

## Quick Start

```python
import asyncio
from chuk_virtual_expert_weather import WeatherExpert, WeatherOperation

expert = WeatherExpert()

# Get forecast for a known city
result = asyncio.run(
    expert.execute_operation_async(
        WeatherOperation.GET_FORECAST.value,
        {"location": "tokyo", "unit": "celsius", "forecast_days": 3},
    )
)
print(result)
```

## Location Aliases

Common city names are resolved automatically (e.g., "tokyo", "nyc", "london", "sf").
Unknown locations can be geocoded first using the `geocode` operation.

## Installation

```bash
pip install chuk-virtual-expert-weather
```

Or in development:

```bash
make dev-install
```
