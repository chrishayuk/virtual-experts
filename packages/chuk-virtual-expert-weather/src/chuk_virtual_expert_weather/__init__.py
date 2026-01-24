"""
chuk-virtual-expert-weather: Weather virtual expert backed by MCP.

Provides weather forecasts, air quality, marine conditions, and historical
weather data via the Open-Meteo MCP server.
"""

from chuk_virtual_expert_weather.expert import (
    LOCATION_ALIASES,
    TEMPERATURE_UNIT_ALIASES,
    PrecipitationUnit,
    TemperatureUnit,
    WeatherExpert,
    WeatherMCPTool,
    WeatherOperation,
    WeatherQueryType,
    WindSpeedUnit,
)
from chuk_virtual_expert_weather.generators import WeatherTraceGenerator

__all__ = [
    "WeatherExpert",
    "WeatherOperation",
    "WeatherMCPTool",
    "WeatherQueryType",
    "TemperatureUnit",
    "WindSpeedUnit",
    "PrecipitationUnit",
    "LOCATION_ALIASES",
    "TEMPERATURE_UNIT_ALIASES",
    "WeatherTraceGenerator",
]

__version__ = "1.0.0"
