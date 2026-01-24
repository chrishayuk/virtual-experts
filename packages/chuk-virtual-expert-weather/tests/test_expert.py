"""Tests for WeatherExpert class."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chuk_virtual_expert_weather import (
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


class TestWeatherOperation:
    """Tests for WeatherOperation enum."""

    def test_values(self) -> None:
        assert WeatherOperation.GET_FORECAST == "get_forecast"
        assert WeatherOperation.GEOCODE == "geocode"
        assert WeatherOperation.GET_HISTORICAL == "get_historical"
        assert WeatherOperation.GET_AIR_QUALITY == "get_air_quality"
        assert WeatherOperation.GET_MARINE == "get_marine"
        assert WeatherOperation.INTERPRET_CODE == "interpret_code"

    def test_count(self) -> None:
        assert len(WeatherOperation) == 6


class TestWeatherMCPTool:
    """Tests for WeatherMCPTool enum."""

    def test_values(self) -> None:
        assert WeatherMCPTool.GET_WEATHER_FORECAST == "get_weather_forecast"
        assert WeatherMCPTool.GEOCODE_LOCATION == "geocode_location"
        assert WeatherMCPTool.GET_HISTORICAL_WEATHER == "get_historical_weather"
        assert WeatherMCPTool.GET_AIR_QUALITY == "get_air_quality"
        assert WeatherMCPTool.GET_MARINE_FORECAST == "get_marine_forecast"
        assert WeatherMCPTool.INTERPRET_WEATHER_CODE == "interpret_weather_code"

    def test_count(self) -> None:
        assert len(WeatherMCPTool) == 6


class TestWeatherQueryType:
    """Tests for WeatherQueryType enum."""

    def test_values(self) -> None:
        assert WeatherQueryType.FORECAST == "forecast"
        assert WeatherQueryType.GEOCODE == "geocode"
        assert WeatherQueryType.HISTORICAL == "historical"
        assert WeatherQueryType.AIR_QUALITY == "air_quality"
        assert WeatherQueryType.MARINE == "marine"
        assert WeatherQueryType.WEATHER_CODE == "weather_code"
        assert WeatherQueryType.ERROR == "error"


class TestWeatherUnits:
    """Tests for unit enums."""

    def test_temperature_units(self) -> None:
        assert TemperatureUnit.CELSIUS == "celsius"
        assert TemperatureUnit.FAHRENHEIT == "fahrenheit"

    def test_wind_speed_units(self) -> None:
        assert WindSpeedUnit.KMH == "kmh"
        assert WindSpeedUnit.MS == "ms"
        assert WindSpeedUnit.MPH == "mph"
        assert WindSpeedUnit.KN == "kn"

    def test_precipitation_units(self) -> None:
        assert PrecipitationUnit.MM == "mm"
        assert PrecipitationUnit.INCH == "inch"


class TestLocationAliases:
    """Tests for LOCATION_ALIASES."""

    def test_has_entries(self) -> None:
        assert len(LOCATION_ALIASES) > 20

    def test_known_cities(self) -> None:
        assert "tokyo" in LOCATION_ALIASES
        assert "london" in LOCATION_ALIASES
        assert "new york" in LOCATION_ALIASES
        assert "sydney" in LOCATION_ALIASES

    def test_alias_structure(self) -> None:
        for _city, coords in LOCATION_ALIASES.items():
            assert "latitude" in coords
            assert "longitude" in coords
            assert -90 <= coords["latitude"] <= 90
            assert -180 <= coords["longitude"] <= 180

    def test_abbreviations(self) -> None:
        assert "nyc" in LOCATION_ALIASES
        assert "la" in LOCATION_ALIASES
        assert "sf" in LOCATION_ALIASES


class TestTemperatureUnitAliases:
    """Tests for TEMPERATURE_UNIT_ALIASES."""

    def test_aliases(self) -> None:
        assert TEMPERATURE_UNIT_ALIASES["f"] == "fahrenheit"
        assert TEMPERATURE_UNIT_ALIASES["c"] == "celsius"
        assert TEMPERATURE_UNIT_ALIASES["fahrenheit"] == "fahrenheit"
        assert TEMPERATURE_UNIT_ALIASES["celsius"] == "celsius"


class TestWeatherExpertClassAttributes:
    """Tests for WeatherExpert class configuration."""

    def test_name(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.name == "weather"

    def test_description(self, weather_expert: WeatherExpert) -> None:
        assert "weather" in weather_expert.description.lower()

    def test_version(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.version == "1.0.0"

    def test_priority(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.priority == 5

    def test_mcp_server_url(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.mcp_server_url == "https://weather.chukai.io/mcp"

    def test_mcp_timeout(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.mcp_timeout == 30.0


class TestCanHandle:
    """Tests for can_handle method."""

    @pytest.mark.parametrize(
        "prompt",
        [
            "What's the weather in Tokyo?",
            "Weather forecast for London",
            "Will it rain tomorrow?",
            "Current temperature in Berlin",
            "Is it snowing in Denver?",
            "Wind speed forecast",
            "Humidity levels today",
            "Air quality in Beijing",
            "Pollution in Mumbai",
            "Marine forecast near Sydney",
            "Ocean conditions today",
            "Wave height forecast",
            "How much precipitation expected?",
            "Is it sunny outside?",
            "Cloudy skies expected",
            "Storm warning in effect",
            "UV index today",
        ],
    )
    def test_handles_weather_queries(self, weather_expert: WeatherExpert, prompt: str) -> None:
        assert weather_expert.can_handle(prompt) is True

    @pytest.mark.parametrize(
        "prompt",
        [
            "What time is it?",
            "Calculate 2 + 2",
            "Tell me a joke",
            "Write a poem",
            "What is the capital of France?",
            "How do I cook pasta?",
            "Convert 3pm EST to PST",
        ],
    )
    def test_rejects_non_weather(self, weather_expert: WeatherExpert, prompt: str) -> None:
        assert weather_expert.can_handle(prompt) is False


class TestGetOperations:
    """Tests for get_operations method."""

    def test_returns_list(self, weather_expert: WeatherExpert) -> None:
        ops = weather_expert.get_operations()
        assert isinstance(ops, list)

    def test_contains_all_operations(self, weather_expert: WeatherExpert) -> None:
        ops = weather_expert.get_operations()
        for op in WeatherOperation:
            assert op.value in ops

    def test_contains_execute_trace(self, weather_expert: WeatherExpert) -> None:
        ops = weather_expert.get_operations()
        assert "execute_trace" in ops


class TestGetMcpToolName:
    """Tests for get_mcp_tool_name method."""

    def test_get_forecast(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.get_mcp_tool_name("get_forecast") == "get_weather_forecast"

    def test_geocode(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.get_mcp_tool_name("geocode") == "geocode_location"

    def test_get_historical(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.get_mcp_tool_name("get_historical") == "get_historical_weather"

    def test_get_air_quality(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.get_mcp_tool_name("get_air_quality") == "get_air_quality"

    def test_get_marine(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.get_mcp_tool_name("get_marine") == "get_marine_forecast"

    def test_interpret_code(self, weather_expert: WeatherExpert) -> None:
        assert weather_expert.get_mcp_tool_name("interpret_code") == "interpret_weather_code"

    def test_unknown_raises(self, weather_expert: WeatherExpert) -> None:
        with pytest.raises(ValueError):
            weather_expert.get_mcp_tool_name("unknown_op")


class TestTransformParameters:
    """Tests for transform_parameters method."""

    def test_forecast_with_alias(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters("get_forecast", {"location": "tokyo"})
        assert result["latitude"] == pytest.approx(35.6762)
        assert result["longitude"] == pytest.approx(139.6503)
        assert result["current_weather"] is True
        assert result["forecast_days"] == 3

    def test_forecast_with_unit_alias(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters(
            "get_forecast", {"location": "london", "unit": "f"}
        )
        assert result["temperature_unit"] == "fahrenheit"

    def test_forecast_with_direct_coords(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters(
            "get_forecast", {"latitude": 48.85, "longitude": 2.35}
        )
        assert result["latitude"] == 48.85
        assert result["longitude"] == 2.35

    def test_geocode_params(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters("geocode", {"name": "Zurich"})
        assert result["name"] == "Zurich"
        assert result["count"] == 1
        assert result["language"] == "en"

    def test_geocode_with_location_key(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters("geocode", {"location": "Zurich"})
        assert result["name"] == "Zurich"

    def test_historical_params(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters(
            "get_historical",
            {"location": "london", "start_date": "2024-01-01", "end_date": "2024-01-07"},
        )
        assert result["latitude"] == pytest.approx(51.5074)
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-07"

    def test_air_quality_params(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters("get_air_quality", {"location": "beijing"})
        assert result["latitude"] == pytest.approx(39.9042)
        assert result["longitude"] == pytest.approx(116.4074)

    def test_marine_params(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters(
            "get_marine", {"location": "miami", "forecast_days": 5}
        )
        assert result["latitude"] == pytest.approx(25.7617)
        assert result["forecast_days"] == 5

    def test_interpret_code_params(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters("interpret_code", {"weather_code": 61})
        assert result["weather_code"] == 61

    def test_interpret_code_alias(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_parameters("interpret_code", {"code": 95})
        assert result["weather_code"] == 95


class TestResolveLocation:
    """Tests for _resolve_location method."""

    def test_alias_resolution(self, weather_expert: WeatherExpert) -> None:
        lat, lon = weather_expert._resolve_location({"location": "Tokyo"})
        assert lat == pytest.approx(35.6762)
        assert lon == pytest.approx(139.6503)

    def test_case_insensitive(self, weather_expert: WeatherExpert) -> None:
        lat, lon = weather_expert._resolve_location({"location": "LONDON"})
        assert lat == pytest.approx(51.5074)

    def test_direct_coords(self, weather_expert: WeatherExpert) -> None:
        lat, lon = weather_expert._resolve_location({"latitude": 40.0, "longitude": -74.0})
        assert lat == 40.0
        assert lon == -74.0

    def test_comma_format(self, weather_expert: WeatherExpert) -> None:
        lat, lon = weather_expert._resolve_location({"location": "48.85, 2.35"})
        assert lat == pytest.approx(48.85)
        assert lon == pytest.approx(2.35)

    def test_empty_raises(self, weather_expert: WeatherExpert) -> None:
        with pytest.raises(ValueError, match="No location provided"):
            weather_expert._resolve_location({})

    def test_unknown_location_raises(self, weather_expert: WeatherExpert) -> None:
        with pytest.raises(ValueError, match="Cannot resolve location"):
            weather_expert._resolve_location({"location": "UnknownPlace123"})


class TestTransformResult:
    """Tests for transform_result method."""

    def test_forecast_result(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_result(
            "get_forecast",
            {
                "latitude": 35.68,
                "longitude": 139.65,
                "elevation": 40.0,
                "timezone": "Asia/Tokyo",
                "current_weather": {"temperature": 15.2},
            },
        )
        assert result["query_type"] == "forecast"
        assert result["latitude"] == 35.68
        assert result["timezone"] == "Asia/Tokyo"
        assert result["current_weather"]["temperature"] == 15.2

    def test_geocode_result(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_result(
            "geocode",
            {
                "results": [
                    {"name": "Paris", "latitude": 48.85, "longitude": 2.35, "country": "France"},
                ],
            },
        )
        assert result["query_type"] == "geocode"
        assert result["count"] == 1
        assert result["locations"][0]["name"] == "Paris"

    def test_historical_result(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_result(
            "get_historical",
            {
                "latitude": 51.5,
                "longitude": -0.13,
                "timezone": "Europe/London",
                "daily": {"temperature_2m_max": [5.0, 6.0]},
            },
        )
        assert result["query_type"] == "historical"
        assert result["daily"]["temperature_2m_max"] == [5.0, 6.0]

    def test_air_quality_result(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_result(
            "get_air_quality",
            {
                "latitude": 39.9,
                "longitude": 116.4,
                "hourly": {"pm2_5": [50.0, 55.0]},
            },
        )
        assert result["query_type"] == "air_quality"
        assert result["hourly"]["pm2_5"] == [50.0, 55.0]

    def test_marine_result(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_result(
            "get_marine",
            {
                "latitude": -33.87,
                "longitude": 151.21,
                "hourly": {"wave_height": [1.2, 1.5]},
            },
        )
        assert result["query_type"] == "marine"
        assert result["hourly"]["wave_height"] == [1.2, 1.5]

    def test_interpret_code_result(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_result(
            "interpret_code",
            {
                "code": 61,
                "description": "Slight rain",
                "severity": "rain",
            },
        )
        assert result["query_type"] == "weather_code"
        assert result["code"] == 61
        assert result["description"] == "Slight rain"
        assert result["severity"] == "rain"

    def test_error_result(self, weather_expert: WeatherExpert) -> None:
        result = weather_expert.transform_result(
            "get_forecast",
            {
                "error": "Connection failed",
            },
        )
        assert result["query_type"] == "error"
        assert result["error"] == "Connection failed"


class TestDataFiles:
    """Tests for data file loading."""

    def test_schema_file_exists(self) -> None:
        path = (
            Path(__file__).parent.parent
            / "src"
            / "chuk_virtual_expert_weather"
            / "data"
            / "schema.json"
        )
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["name"] == "weather"
        assert "operations" in data
        assert len(data["operations"]) == 6

    def test_calibration_file_exists(self) -> None:
        path = (
            Path(__file__).parent.parent
            / "src"
            / "chuk_virtual_expert_weather"
            / "data"
            / "calibration.json"
        )
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["name"] == "weather"
        assert len(data["positive"]) == 20

    def test_cot_examples_file_exists(self) -> None:
        path = (
            Path(__file__).parent.parent
            / "src"
            / "chuk_virtual_expert_weather"
            / "data"
            / "cot_examples.json"
        )
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["expert_name"] == "weather"
        assert len(data["examples"]) >= 15

    def test_cot_examples_have_correct_structure(self) -> None:
        path = (
            Path(__file__).parent.parent
            / "src"
            / "chuk_virtual_expert_weather"
            / "data"
            / "cot_examples.json"
        )
        data = json.loads(path.read_text())
        for example in data["examples"]:
            assert "query" in example
            assert "action" in example
            action = example["action"]
            assert "expert" in action
            assert "operation" in action
            assert "parameters" in action
            assert "confidence" in action
            assert "reasoning" in action

    def test_calibration_positive_weather_related(self) -> None:
        path = (
            Path(__file__).parent.parent
            / "src"
            / "chuk_virtual_expert_weather"
            / "data"
            / "calibration.json"
        )
        data = json.loads(path.read_text())
        weather_keywords = [
            "weather",
            "rain",
            "temperature",
            "forecast",
            "air",
            "ocean",
            "marine",
            "wind",
            "snow",
            "sunny",
            "cloudy",
            "storm",
            "humidity",
            "pollution",
            "uv",
            "precipitation",
        ]
        for prompt in data["positive"]:
            assert any(kw in prompt.lower() for kw in weather_keywords), (
                f"Positive example not weather-related: {prompt}"
            )
