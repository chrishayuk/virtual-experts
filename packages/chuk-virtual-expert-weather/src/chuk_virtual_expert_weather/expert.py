"""
Weather virtual expert backed by MCP server.

Pydantic-native, async-native, no magic strings.
Delegates to the hosted MCP weather server at https://weather.chukai.io/mcp
"""

from __future__ import annotations

from enum import Enum
from typing import Any, ClassVar

from chuk_virtual_expert.mcp_expert import MCPExpert
from chuk_virtual_expert.models import TraceResult


class WeatherOperation(str, Enum):
    """Operations supported by the weather expert."""

    GET_FORECAST = "get_forecast"
    GEOCODE = "geocode"
    GET_HISTORICAL = "get_historical"
    GET_AIR_QUALITY = "get_air_quality"
    GET_MARINE = "get_marine"
    INTERPRET_CODE = "interpret_code"


class WeatherMCPTool(str, Enum):
    """MCP tool names from chuk-mcp-open-meteo server."""

    GET_WEATHER_FORECAST = "get_weather_forecast"
    GEOCODE_LOCATION = "geocode_location"
    GET_HISTORICAL_WEATHER = "get_historical_weather"
    GET_AIR_QUALITY = "get_air_quality"
    GET_MARINE_FORECAST = "get_marine_forecast"
    INTERPRET_WEATHER_CODE = "interpret_weather_code"


class WeatherQueryType(str, Enum):
    """Query result types for weather expert."""

    FORECAST = "forecast"
    GEOCODE = "geocode"
    HISTORICAL = "historical"
    AIR_QUALITY = "air_quality"
    MARINE = "marine"
    WEATHER_CODE = "weather_code"
    ERROR = "error"


class TemperatureUnit(str, Enum):
    """Temperature unit options."""

    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


class WindSpeedUnit(str, Enum):
    """Wind speed unit options."""

    KMH = "kmh"
    MS = "ms"
    MPH = "mph"
    KN = "kn"


class PrecipitationUnit(str, Enum):
    """Precipitation unit options."""

    MM = "mm"
    INCH = "inch"


# Location aliases for common cities (used for parameter normalization)
LOCATION_ALIASES: dict[str, dict[str, float]] = {
    # North America
    "new york": {"latitude": 40.7128, "longitude": -74.0060},
    "nyc": {"latitude": 40.7128, "longitude": -74.0060},
    "los angeles": {"latitude": 34.0522, "longitude": -118.2437},
    "la": {"latitude": 34.0522, "longitude": -118.2437},
    "chicago": {"latitude": 41.8781, "longitude": -87.6298},
    "san francisco": {"latitude": 37.7749, "longitude": -122.4194},
    "sf": {"latitude": 37.7749, "longitude": -122.4194},
    "miami": {"latitude": 25.7617, "longitude": -80.1918},
    "seattle": {"latitude": 47.6062, "longitude": -122.3321},
    "denver": {"latitude": 39.7392, "longitude": -104.9903},
    "toronto": {"latitude": 43.6532, "longitude": -79.3832},
    "mexico city": {"latitude": 19.4326, "longitude": -99.1332},
    # Europe
    "london": {"latitude": 51.5074, "longitude": -0.1278},
    "paris": {"latitude": 48.8566, "longitude": 2.3522},
    "berlin": {"latitude": 52.5200, "longitude": 13.4050},
    "amsterdam": {"latitude": 52.3676, "longitude": 4.9041},
    "rome": {"latitude": 41.9028, "longitude": 12.4964},
    "madrid": {"latitude": 40.4168, "longitude": -3.7038},
    "moscow": {"latitude": 55.7558, "longitude": 37.6173},
    # Asia
    "tokyo": {"latitude": 35.6762, "longitude": 139.6503},
    "beijing": {"latitude": 39.9042, "longitude": 116.4074},
    "shanghai": {"latitude": 31.2304, "longitude": 121.4737},
    "singapore": {"latitude": 1.3521, "longitude": 103.8198},
    "mumbai": {"latitude": 19.0760, "longitude": 72.8777},
    "dubai": {"latitude": 25.2048, "longitude": 55.2708},
    "bangkok": {"latitude": 13.7563, "longitude": 100.5018},
    "seoul": {"latitude": 37.5665, "longitude": 126.9780},
    "hong kong": {"latitude": 22.3193, "longitude": 114.1694},
    # Oceania
    "sydney": {"latitude": -33.8688, "longitude": 151.2093},
    # South America
    "sao paulo": {"latitude": -23.5505, "longitude": -46.6333},
    # Africa
    "cairo": {"latitude": 30.0444, "longitude": 31.2357},
}

# Temperature unit aliases for user-friendly input
TEMPERATURE_UNIT_ALIASES: dict[str, str] = {
    "fahrenheit": TemperatureUnit.FAHRENHEIT.value,
    "f": TemperatureUnit.FAHRENHEIT.value,
    "celsius": TemperatureUnit.CELSIUS.value,
    "c": TemperatureUnit.CELSIUS.value,
}


class WeatherExpert(MCPExpert):
    """
    Virtual expert for weather, air quality, and marine conditions.

    Delegates to the hosted MCP weather server (Open-Meteo) for live data.

    Operations:
        - get_forecast: Get current weather and forecast for a location
        - geocode: Convert a location name to coordinates
        - get_historical: Get historical weather data (from 1940+)
        - get_air_quality: Get air quality and pollutant data
        - get_marine: Get marine/ocean weather forecast
        - interpret_code: Interpret a WMO weather code
    """

    # Class configuration
    name: ClassVar[str] = "weather"
    description: ClassVar[str] = (
        "Get weather forecasts, air quality, marine conditions, and historical weather data"
    )
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 5

    # MCP server configuration
    mcp_server_url: ClassVar[str] = "https://weather.chukai.io/mcp"
    mcp_timeout: ClassVar[float] = 30.0

    # File paths for CoT examples and schema (in data/ subdirectory)
    cot_examples_file: ClassVar[str] = "data/cot_examples.json"
    schema_file: ClassVar[str] = "data/schema.json"
    calibration_file: ClassVar[str] = "data/calibration.json"

    # Keywords for can_handle check
    _WEATHER_KEYWORDS: ClassVar[list[str]] = [
        "weather",
        "forecast",
        "temperature",
        "rain",
        "snow",
        "wind",
        "humidity",
        "air quality",
        "pollution",
        "marine",
        "ocean",
        "wave",
        "precipitation",
        "sunny",
        "cloudy",
        "storm",
        "hail",
        "uv index",
    ]

    def can_handle(self, prompt: str) -> bool:
        """
        Check if this expert can handle the given prompt.

        Uses weather-related keywords for fast pre-filtering.
        """
        prompt_lower = prompt.lower()
        return any(kw in prompt_lower for kw in self._WEATHER_KEYWORDS)

    def get_operations(self) -> list[str]:
        """Return list of available operations."""
        return [op.value for op in WeatherOperation] + ["execute_trace"]

    def get_mcp_tool_name(self, operation: str) -> str:
        """Map virtual expert operation to MCP tool name."""
        op = WeatherOperation(operation)

        mapping: dict[WeatherOperation, WeatherMCPTool] = {
            WeatherOperation.GET_FORECAST: WeatherMCPTool.GET_WEATHER_FORECAST,
            WeatherOperation.GEOCODE: WeatherMCPTool.GEOCODE_LOCATION,
            WeatherOperation.GET_HISTORICAL: WeatherMCPTool.GET_HISTORICAL_WEATHER,
            WeatherOperation.GET_AIR_QUALITY: WeatherMCPTool.GET_AIR_QUALITY,
            WeatherOperation.GET_MARINE: WeatherMCPTool.GET_MARINE_FORECAST,
            WeatherOperation.INTERPRET_CODE: WeatherMCPTool.INTERPRET_WEATHER_CODE,
        }

        tool = mapping.get(op)
        if not tool:
            raise ValueError(f"Unknown operation: {operation}")

        return tool.value

    def transform_parameters(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Transform virtual expert parameters to MCP tool arguments."""
        op = WeatherOperation(operation)

        if op == WeatherOperation.GET_FORECAST:
            return self._transform_forecast_params(parameters)
        elif op == WeatherOperation.GEOCODE:
            return self._transform_geocode_params(parameters)
        elif op == WeatherOperation.GET_HISTORICAL:
            return self._transform_historical_params(parameters)
        elif op == WeatherOperation.GET_AIR_QUALITY:
            return self._transform_air_quality_params(parameters)
        elif op == WeatherOperation.GET_MARINE:
            return self._transform_marine_params(parameters)
        elif op == WeatherOperation.INTERPRET_CODE:
            return self._transform_interpret_code_params(parameters)

        return parameters

    def transform_result(self, operation: str, tool_result: dict[str, Any]) -> dict[str, Any]:
        """Transform MCP tool result to virtual expert format."""
        op = WeatherOperation(operation)

        # Handle error results
        if "error" in tool_result:
            return {
                "query_type": WeatherQueryType.ERROR.value,
                "error": tool_result["error"],
            }

        if op == WeatherOperation.GET_FORECAST:
            return self._transform_forecast_result(tool_result)
        elif op == WeatherOperation.GEOCODE:
            return self._transform_geocode_result(tool_result)
        elif op == WeatherOperation.GET_HISTORICAL:
            return self._transform_historical_result(tool_result)
        elif op == WeatherOperation.GET_AIR_QUALITY:
            return self._transform_air_quality_result(tool_result)
        elif op == WeatherOperation.GET_MARINE:
            return self._transform_marine_result(tool_result)
        elif op == WeatherOperation.INTERPRET_CODE:
            return self._transform_interpret_code_result(tool_result)

        return tool_result

    # ─── Parameter Transformers ───────────────────────────────────────────────

    def _transform_forecast_params(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Transform get_forecast parameters."""
        lat, lon = self._resolve_location(parameters)
        result: dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": parameters.get("current_weather", True),
            "forecast_days": parameters.get("forecast_days", 3),
        }

        # Resolve temperature unit alias
        unit = parameters.get("unit", parameters.get("temperature_unit", ""))
        if unit:
            resolved = TEMPERATURE_UNIT_ALIASES.get(str(unit).lower(), str(unit))
            result["temperature_unit"] = resolved

        # Pass through optional params
        for key in ("hourly", "daily", "wind_speed_unit", "precipitation_unit", "timezone"):
            if key in parameters:
                result[key] = parameters[key]

        return result

    def _transform_geocode_params(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Transform geocode parameters."""
        return {
            "name": parameters.get("name", parameters.get("location", "")),
            "count": parameters.get("count", 1),
            "language": parameters.get("language", "en"),
        }

    def _transform_historical_params(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Transform get_historical parameters."""
        lat, lon = self._resolve_location(parameters)
        result: dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "start_date": parameters.get("start_date", ""),
            "end_date": parameters.get("end_date", ""),
        }

        for key in ("hourly", "daily", "temperature_unit", "timezone"):
            if key in parameters:
                result[key] = parameters[key]

        return result

    def _transform_air_quality_params(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Transform get_air_quality parameters."""
        lat, lon = self._resolve_location(parameters)
        result: dict[str, Any] = {"latitude": lat, "longitude": lon}

        for key in ("hourly", "timezone", "domains"):
            if key in parameters:
                result[key] = parameters[key]

        return result

    def _transform_marine_params(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Transform get_marine parameters."""
        lat, lon = self._resolve_location(parameters)
        result: dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "forecast_days": parameters.get("forecast_days", 3),
        }

        for key in ("hourly", "daily", "timezone"):
            if key in parameters:
                result[key] = parameters[key]

        return result

    def _transform_interpret_code_params(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Transform interpret_code parameters."""
        return {
            "weather_code": parameters.get("weather_code", parameters.get("code", 0)),
        }

    # ─── Result Transformers ──────────────────────────────────────────────────

    def _transform_forecast_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Transform get_weather_forecast MCP result."""
        return {
            "query_type": WeatherQueryType.FORECAST.value,
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "elevation": result.get("elevation"),
            "timezone": result.get("timezone", ""),
            "current_weather": result.get("current_weather", {}),
            "hourly": result.get("hourly", {}),
            "daily": result.get("daily", {}),
        }

    def _transform_geocode_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Transform geocode_location MCP result."""
        results = result.get("results", [])
        locations = []
        for loc in results:
            locations.append(
                {
                    "name": loc.get("name", ""),
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                    "country": loc.get("country", ""),
                    "admin1": loc.get("admin1", ""),
                    "timezone": loc.get("timezone", ""),
                }
            )
        return {
            "query_type": WeatherQueryType.GEOCODE.value,
            "locations": locations,
            "count": len(locations),
        }

    def _transform_historical_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Transform get_historical_weather MCP result."""
        return {
            "query_type": WeatherQueryType.HISTORICAL.value,
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "timezone": result.get("timezone", ""),
            "hourly": result.get("hourly", {}),
            "daily": result.get("daily", {}),
        }

    def _transform_air_quality_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Transform get_air_quality MCP result."""
        return {
            "query_type": WeatherQueryType.AIR_QUALITY.value,
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "hourly": result.get("hourly", {}),
        }

    def _transform_marine_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Transform get_marine_forecast MCP result."""
        return {
            "query_type": WeatherQueryType.MARINE.value,
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "timezone": result.get("timezone", ""),
            "hourly": result.get("hourly", {}),
            "daily": result.get("daily", {}),
        }

    def _transform_interpret_code_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Transform interpret_weather_code MCP result."""
        return {
            "query_type": WeatherQueryType.WEATHER_CODE.value,
            "code": result.get("code", result.get("weather_code")),
            "description": result.get("description", ""),
            "severity": result.get("severity", ""),
        }

    # ─── Location Resolution ─────────────────────────────────────────────────

    def _resolve_location(self, parameters: dict[str, Any]) -> tuple[float, float]:
        """
        Resolve location parameters to (latitude, longitude).

        Supports:
          - Direct latitude/longitude parameters
          - Named location via LOCATION_ALIASES
          - Comma-separated "lat,lon" string
        """
        # Direct lat/lon provided
        if "latitude" in parameters and "longitude" in parameters:
            return float(parameters["latitude"]), float(parameters["longitude"])

        # Location string
        location = str(parameters.get("location", ""))
        if not location:
            raise ValueError("No location provided. Specify latitude/longitude or a location name.")

        # Check aliases (case-insensitive)
        lookup = location.strip().lower()
        if lookup in LOCATION_ALIASES:
            coords = LOCATION_ALIASES[lookup]
            return coords["latitude"], coords["longitude"]

        # Try to parse "lat,lon" format
        if "," in location:
            parts = location.split(",")
            if len(parts) == 2:
                try:
                    return float(parts[0].strip()), float(parts[1].strip())
                except ValueError:
                    pass

        raise ValueError(
            f"Cannot resolve location '{location}'. "
            "Use a known city name, 'lat,lon' format, or geocode first."
        )

    # ─── Trace Execution ──────────────────────────────────────────────────────

    def execute_operation(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an operation, intercepting execute_trace locally."""
        if operation == "execute_trace":
            import asyncio

            trace_steps = parameters.get("trace", [])
            result = asyncio.run(self._execute_trace_async(trace_steps))
            return {
                "success": result.success,
                "answer": result.answer,
                "state": result.state,
                "error": result.error,
                "steps_executed": result.steps_executed,
                "formatted": str(result.answer) if result.answer is not None else "",
            }
        return super().execute_operation(operation, parameters)

    async def execute_operation_async(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an operation async, intercepting execute_trace locally."""
        if operation == "execute_trace":
            trace_steps = parameters.get("trace", [])
            result = await self._execute_trace_async(trace_steps)
            return {
                "success": result.success,
                "answer": result.answer,
                "state": result.state,
                "error": result.error,
                "steps_executed": result.steps_executed,
                "formatted": str(result.answer) if result.answer is not None else "",
            }
        return await super().execute_operation_async(operation, parameters)

    async def _execute_trace_async(self, steps: list[dict[str, Any]]) -> TraceResult:
        """
        Execute a sequence of weather trace steps.

        Handles:
        - init: Set a variable to a literal value
        - geocode: Call MCP geocode_location, store result in variable
        - get_forecast: Call MCP get_weather_forecast, store result
        - get_historical: Call MCP get_historical_weather, store result
        - get_air_quality: Call MCP get_air_quality, store result
        - get_marine: Call MCP get_marine_forecast, store result
        - interpret_code: Call MCP interpret_weather_code, store result
        - query: Specify which variable to return
        """
        state: dict[str, Any] = {}
        query_var: str | None = None
        steps_executed = 0

        for i, step in enumerate(steps):
            try:
                op = next(iter(step))

                if op == "init":
                    var = step["init"]
                    state[var] = step.get("value")

                elif op == "geocode":
                    params = step["geocode"]
                    name = params.get("name", "")
                    var = params.get("var", "result")
                    result = await super().execute_operation_async(
                        WeatherOperation.GEOCODE.value,
                        {"name": name},
                    )
                    state[var] = result

                elif op == "get_forecast":
                    params = step["get_forecast"]
                    call_params = self._build_location_params(params, state)
                    # Pass through extra params
                    for key in (
                        "forecast_days",
                        "unit",
                        "temperature_unit",
                        "hourly",
                        "daily",
                        "timezone",
                    ):
                        if key in params:
                            call_params[key] = params[key]
                    var = params.get("var", "result")
                    result = await super().execute_operation_async(
                        WeatherOperation.GET_FORECAST.value,
                        call_params,
                    )
                    state[var] = result

                elif op == "get_historical":
                    params = step["get_historical"]
                    call_params = self._build_location_params(params, state)
                    for key in ("start_date", "end_date", "hourly", "daily", "timezone"):
                        if key in params:
                            call_params[key] = params[key]
                    var = params.get("var", "result")
                    result = await super().execute_operation_async(
                        WeatherOperation.GET_HISTORICAL.value,
                        call_params,
                    )
                    state[var] = result

                elif op == "get_air_quality":
                    params = step["get_air_quality"]
                    call_params = self._build_location_params(params, state)
                    for key in ("hourly", "timezone", "domains"):
                        if key in params:
                            call_params[key] = params[key]
                    var = params.get("var", "result")
                    result = await super().execute_operation_async(
                        WeatherOperation.GET_AIR_QUALITY.value,
                        call_params,
                    )
                    state[var] = result

                elif op == "get_marine":
                    params = step["get_marine"]
                    call_params = self._build_location_params(params, state)
                    for key in ("forecast_days", "hourly", "daily", "timezone"):
                        if key in params:
                            call_params[key] = params[key]
                    var = params.get("var", "result")
                    result = await super().execute_operation_async(
                        WeatherOperation.GET_MARINE.value,
                        call_params,
                    )
                    state[var] = result

                elif op == "interpret_code":
                    params = step["interpret_code"]
                    code = params.get("weather_code", params.get("code", 0))
                    var = params.get("var", "result")
                    result = await super().execute_operation_async(
                        WeatherOperation.INTERPRET_CODE.value,
                        {"weather_code": code},
                    )
                    state[var] = result

                elif op == "query":
                    query_var = step["query"]

                else:
                    return TraceResult(
                        success=False,
                        error=f"Step {i}: Unknown weather operation: {op}",
                        state=state,
                        expert=self.name,
                        steps_executed=steps_executed,
                    )

                steps_executed += 1

            except Exception as e:
                return TraceResult(
                    success=False,
                    error=f"Step {i}: {e}",
                    state=state,
                    expert=self.name,
                    steps_executed=steps_executed,
                )

        # Resolve answer
        answer = state.get(query_var) if query_var else None

        return TraceResult(
            success=True,
            answer=answer,
            state=state,
            expert=self.name,
            steps_executed=steps_executed,
        )

    def _build_location_params(
        self, params: dict[str, Any], state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Build location parameters for a trace step.

        Supports:
          - Direct location/latitude/longitude in params
          - location_var referencing a geocoded result in state
        """
        if "location_var" in params and params["location_var"] in state:
            geocode_result = state[params["location_var"]]
            if isinstance(geocode_result, dict):
                # Handle transformed geocode result (has "locations" list)
                locations = geocode_result.get("locations", [])
                if locations:
                    first = locations[0]
                    return {
                        "latitude": first.get("latitude"),
                        "longitude": first.get("longitude"),
                    }
                # Handle raw result
                if "latitude" in geocode_result and "longitude" in geocode_result:
                    return {
                        "latitude": geocode_result["latitude"],
                        "longitude": geocode_result["longitude"],
                    }
            raise ValueError(
                f"Cannot extract coordinates from location_var '{params['location_var']}'"
            )

        # Build from direct params
        result: dict[str, Any] = {}
        if "latitude" in params and "longitude" in params:
            result["latitude"] = params["latitude"]
            result["longitude"] = params["longitude"]
        elif "location" in params:
            result["location"] = params["location"]

        return result
