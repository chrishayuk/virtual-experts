"""Tests for weather trace execution and WeatherTraceGenerator."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from chuk_virtual_expert_weather import WeatherExpert, WeatherTraceGenerator
from chuk_virtual_expert_weather.expert import LOCATION_ALIASES, WeatherOperation


class TestWeatherTraceExecution:
    """Tests for trace execution via execute_operation."""

    @pytest.fixture
    def expert(self) -> WeatherExpert:
        return WeatherExpert()

    def test_init_and_query(self, expert: WeatherExpert) -> None:
        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"init": "city", "value": "Tokyo"},
                    {"query": "city"},
                ],
            },
        )
        assert result["success"] is True
        assert result["answer"] == "Tokyo"
        assert result["steps_executed"] == 2

    def test_empty_trace(self, expert: WeatherExpert) -> None:
        result = expert.execute_operation("execute_trace", {"trace": []})
        assert result["success"] is True
        assert result["answer"] is None
        assert result["steps_executed"] == 0

    def test_unknown_step_fails(self, expert: WeatherExpert) -> None:
        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [{"unknown_op": {"foo": "bar"}}],
            },
        )
        assert result["success"] is False
        assert "Unknown weather operation" in result["error"]

    def test_query_nonexistent_var(self, expert: WeatherExpert) -> None:
        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"init": "x", "value": 1},
                    {"query": "y"},
                ],
            },
        )
        assert result["success"] is True
        assert result["answer"] is None

    @patch.object(WeatherExpert, "execute_operation_async", new_callable=AsyncMock)
    def test_geocode_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "geocode",
            "locations": [{"name": "Zurich", "latitude": 47.37, "longitude": 8.54}],
            "count": 1,
        }

        # Call the actual trace execution (which internally calls super)
        with patch(
            "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
            new_callable=AsyncMock,
            return_value={
                "query_type": "geocode",
                "locations": [{"name": "Zurich", "latitude": 47.37, "longitude": 8.54}],
                "count": 1,
            },
        ):
            result = expert.execute_operation(
                "execute_trace",
                {
                    "trace": [
                        {"geocode": {"name": "Zurich", "var": "loc"}},
                        {"query": "loc"},
                    ],
                },
            )

        assert result["success"] is True
        assert result["answer"]["locations"][0]["name"] == "Zurich"

    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
        new_callable=AsyncMock,
    )
    def test_get_forecast_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "forecast",
            "latitude": 35.68,
            "longitude": 139.65,
            "current_weather": {"temperature": 20.5},
        }

        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"get_forecast": {"location": "tokyo", "var": "weather"}},
                    {"query": "weather"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["current_weather"]["temperature"] == 20.5

    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
        new_callable=AsyncMock,
    )
    def test_multi_step_geocode_then_forecast(
        self, mock_exec: AsyncMock, expert: WeatherExpert
    ) -> None:
        geocode_result = {
            "query_type": "geocode",
            "locations": [{"name": "Zurich", "latitude": 47.37, "longitude": 8.54}],
            "count": 1,
        }
        forecast_result = {
            "query_type": "forecast",
            "latitude": 47.37,
            "longitude": 8.54,
            "current_weather": {"temperature": 12.0},
        }

        mock_exec.side_effect = [geocode_result, forecast_result]

        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"geocode": {"name": "Zurich", "var": "loc"}},
                    {"get_forecast": {"location_var": "loc", "var": "weather"}},
                    {"query": "weather"},
                ],
            },
        )

        assert result["success"] is True
        assert result["steps_executed"] == 3
        assert result["answer"]["current_weather"]["temperature"] == 12.0

    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
        new_callable=AsyncMock,
    )
    def test_air_quality_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "air_quality",
            "latitude": 39.9,
            "longitude": 116.4,
            "hourly": {"pm2_5": [50.0]},
        }

        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"get_air_quality": {"location": "beijing", "var": "aqi"}},
                    {"query": "aqi"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["hourly"]["pm2_5"] == [50.0]

    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
        new_callable=AsyncMock,
    )
    def test_marine_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "marine",
            "latitude": -33.87,
            "longitude": 151.21,
            "hourly": {"wave_height": [1.5]},
        }

        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"get_marine": {"location": "sydney", "var": "marine"}},
                    {"query": "marine"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["hourly"]["wave_height"] == [1.5]

    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
        new_callable=AsyncMock,
    )
    def test_interpret_code_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "weather_code",
            "code": 61,
            "description": "Slight rain",
            "severity": "rain",
        }

        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"interpret_code": {"weather_code": 61, "var": "code_info"}},
                    {"query": "code_info"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["description"] == "Slight rain"

    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
        new_callable=AsyncMock,
    )
    def test_historical_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "historical",
            "latitude": 51.5,
            "longitude": -0.13,
            "daily": {"temperature_2m_max": [5.0, 6.0]},
        }

        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {
                        "get_historical": {
                            "location": "london",
                            "start_date": "2024-01-01",
                            "end_date": "2024-01-02",
                            "var": "history",
                        }
                    },
                    {"query": "history"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["daily"]["temperature_2m_max"] == [5.0, 6.0]

    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
        new_callable=AsyncMock,
    )
    def test_mcp_error_in_trace(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.side_effect = Exception("Connection refused")

        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"get_forecast": {"location": "tokyo", "var": "weather"}},
                    {"query": "weather"},
                ],
            },
        )

        assert result["success"] is False
        assert "Connection refused" in result["error"]
        assert result["steps_executed"] == 0

    def test_formatted_output(self, expert: WeatherExpert) -> None:
        result = expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"init": "temp", "value": 25.5},
                    {"query": "temp"},
                ],
            },
        )
        assert result["formatted"] == "25.5"

    def test_formatted_none(self, expert: WeatherExpert) -> None:
        result = expert.execute_operation("execute_trace", {"trace": []})
        assert result["formatted"] == ""


class TestWeatherTraceAsync:
    """Tests for async trace execution."""

    @pytest.fixture
    def expert(self) -> WeatherExpert:
        return WeatherExpert()

    @pytest.mark.asyncio
    async def test_async_trace_execution(self, expert: WeatherExpert) -> None:
        result = await expert.execute_operation_async(
            "execute_trace",
            {
                "trace": [
                    {"init": "val", "value": 42},
                    {"query": "val"},
                ],
            },
        )
        assert result["success"] is True
        assert result["answer"] == 42

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation_async",
        new_callable=AsyncMock,
    )
    async def test_async_non_trace_delegates(
        self, mock_exec: AsyncMock, expert: WeatherExpert
    ) -> None:
        mock_exec.return_value = {"query_type": "forecast", "latitude": 35.68}

        result = await expert.execute_operation_async("get_forecast", {"location": "tokyo"})

        assert result["query_type"] == "forecast"
        mock_exec.assert_called_once()


class TestBuildLocationParams:
    """Tests for _build_location_params helper."""

    @pytest.fixture
    def expert(self) -> WeatherExpert:
        return WeatherExpert()

    def test_direct_location(self, expert: WeatherExpert) -> None:
        result = expert._build_location_params({"location": "tokyo"}, {})
        assert result["location"] == "tokyo"

    def test_direct_coords(self, expert: WeatherExpert) -> None:
        result = expert._build_location_params({"latitude": 40.0, "longitude": -74.0}, {})
        assert result["latitude"] == 40.0
        assert result["longitude"] == -74.0

    def test_location_var_from_geocode(self, expert: WeatherExpert) -> None:
        state: dict[str, Any] = {
            "loc": {
                "query_type": "geocode",
                "locations": [{"name": "Zurich", "latitude": 47.37, "longitude": 8.54}],
                "count": 1,
            }
        }
        result = expert._build_location_params({"location_var": "loc"}, state)
        assert result["latitude"] == 47.37
        assert result["longitude"] == 8.54

    def test_location_var_missing_raises(self, expert: WeatherExpert) -> None:
        state: dict[str, Any] = {"loc": {"no_locations": True}}
        with pytest.raises(ValueError, match="Cannot extract coordinates"):
            expert._build_location_params({"location_var": "loc"}, state)


class TestWeatherTraceGenerator:
    """Tests for WeatherTraceGenerator."""

    @pytest.fixture
    def generator(self) -> WeatherTraceGenerator:
        return WeatherTraceGenerator(seed=42)

    def test_generate_get_forecast(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_get_forecast(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expert"] == "weather"
            assert ex["expected_operation"] == WeatherOperation.GET_FORECAST.value
            assert "trace" in ex
            assert "query" in ex

    def test_generate_geocode(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_geocode(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expected_operation"] == WeatherOperation.GEOCODE.value

    def test_generate_get_historical(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_get_historical(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expected_operation"] == WeatherOperation.GET_HISTORICAL.value
            params = ex["expected_params"]
            assert "start_date" in params
            assert "end_date" in params

    def test_generate_get_air_quality(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_get_air_quality(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expected_operation"] == WeatherOperation.GET_AIR_QUALITY.value

    def test_generate_get_marine(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_get_marine(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["expected_operation"] == WeatherOperation.GET_MARINE.value

    def test_generate_multi_step(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_multi_step(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex["multi_step"] is True
            trace = ex["trace"]
            assert trace[0].get("geocode") is not None
            assert trace[1].get("get_forecast") is not None

    def test_generate_all(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_all(n_per_type=3)
        # 6 types * 3 each = 18
        assert len(examples) == 18

    def test_reproducibility(self) -> None:
        gen1 = WeatherTraceGenerator(seed=123)
        gen2 = WeatherTraceGenerator(seed=123)
        assert gen1.generate_get_forecast(5) == gen2.generate_get_forecast(5)

    def test_different_seeds(self) -> None:
        gen1 = WeatherTraceGenerator(seed=1)
        gen2 = WeatherTraceGenerator(seed=2)
        # Very unlikely to be identical
        r1 = gen1.generate_get_forecast(10)
        r2 = gen2.generate_get_forecast(10)
        assert r1 != r2

    def test_get_location_aliases(self) -> None:
        aliases = WeatherTraceGenerator.get_location_aliases()
        assert aliases is LOCATION_ALIASES
        assert "tokyo" in aliases

    def test_queries_are_natural_language(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_get_forecast(5)
        for ex in examples:
            query = ex["query"]
            assert len(query) > 10
            assert any(c.isalpha() for c in query)
