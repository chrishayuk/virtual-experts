"""Tests for weather trace execution and WeatherTraceGenerator."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from chuk_virtual_expert.trace_models import (
    GeocodeStep,
    GetForecastStep,
    QueryStep,
)

from chuk_virtual_expert_weather import WeatherExpert, WeatherTraceGenerator
from chuk_virtual_expert_weather.expert import LOCATION_ALIASES, WeatherOperation


class TestWeatherTraceExecution:
    """Tests for trace execution via execute_operation."""

    @pytest.fixture
    def expert(self) -> WeatherExpert:
        return WeatherExpert()

    @pytest.mark.asyncio
    async def test_init_and_query(self, expert: WeatherExpert) -> None:
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "city", "value": "Tokyo"},
                    {"op": "query", "var": "city"},
                ],
            },
        )
        assert result["success"] is True
        assert result["answer"] == "Tokyo"
        assert result["steps_executed"] == 2

    @pytest.mark.asyncio
    async def test_empty_trace(self, expert: WeatherExpert) -> None:
        result = await expert.execute_operation("execute_trace", {"trace": []})
        assert result["success"] is True
        assert result["answer"] is None
        assert result["steps_executed"] == 0

    @pytest.mark.asyncio
    async def test_unknown_step_fails(self, expert: WeatherExpert) -> None:
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [{"op": "compute", "compute_op": "add", "args": [1, 2], "var": "r"}],
            },
        )
        # ComputeStep is not handled by weather expert — falls through to else branch
        assert result["success"] is False
        assert "Unknown weather step type" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_step_parse_error(self, expert: WeatherExpert) -> None:
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [{"op": "unknown_op_xyz"}],
            },
        )
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_query_nonexistent_var(self, expert: WeatherExpert) -> None:
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "x", "value": 1},
                    {"op": "query", "var": "y"},
                ],
            },
        )
        assert result["success"] is True
        assert result["answer"] is None

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_geocode_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "geocode",
            "locations": [{"name": "Zurich", "latitude": 47.37, "longitude": 8.54}],
            "count": 1,
        }

        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "geocode", "name": "Zurich", "var": "loc"},
                    {"op": "query", "var": "loc"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["locations"][0]["name"] == "Zurich"

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_get_forecast_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "forecast",
            "latitude": 35.68,
            "longitude": 139.65,
            "current_weather": {"temperature": 20.5},
        }

        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "get_forecast", "location": "tokyo", "var": "weather"},
                    {"op": "query", "var": "weather"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["current_weather"]["temperature"] == 20.5

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_multi_step_geocode_then_forecast(
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

        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "geocode", "name": "Zurich", "var": "loc"},
                    {"op": "get_forecast", "location_var": "loc", "var": "weather"},
                    {"op": "query", "var": "weather"},
                ],
            },
        )

        assert result["success"] is True
        assert result["steps_executed"] == 3
        assert result["answer"]["current_weather"]["temperature"] == 12.0

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_air_quality_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "air_quality",
            "latitude": 39.9,
            "longitude": 116.4,
            "hourly": {"pm2_5": [50.0]},
        }

        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "get_air_quality", "location": "beijing", "var": "aqi"},
                    {"op": "query", "var": "aqi"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["hourly"]["pm2_5"] == [50.0]

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_marine_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "marine",
            "latitude": -33.87,
            "longitude": 151.21,
            "hourly": {"wave_height": [1.5]},
        }

        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "get_marine", "location": "sydney", "var": "marine"},
                    {"op": "query", "var": "marine"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["hourly"]["wave_height"] == [1.5]

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_interpret_code_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "weather_code",
            "code": 61,
            "description": "Slight rain",
            "severity": "rain",
        }

        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "interpret_code", "weather_code": 61, "var": "code_info"},
                    {"op": "query", "var": "code_info"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["description"] == "Slight rain"

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_historical_step(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {
            "query_type": "historical",
            "latitude": 51.5,
            "longitude": -0.13,
            "daily": {"temperature_2m_max": [5.0, 6.0]},
        }

        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {
                        "op": "get_historical",
                        "location": "london",
                        "start_date": "2024-01-01",
                        "end_date": "2024-01-02",
                        "var": "history",
                    },
                    {"op": "query", "var": "history"},
                ],
            },
        )

        assert result["success"] is True
        assert result["answer"]["daily"]["temperature_2m_max"] == [5.0, 6.0]

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_mcp_error_in_trace(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.side_effect = Exception("Connection refused")

        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "get_forecast", "location": "tokyo", "var": "weather"},
                    {"op": "query", "var": "weather"},
                ],
            },
        )

        assert result["success"] is False
        assert "Connection refused" in result["error"]
        assert result["steps_executed"] == 0

    @pytest.mark.asyncio
    async def test_formatted_output(self, expert: WeatherExpert) -> None:
        result = await expert.execute_operation(
            "execute_trace",
            {
                "trace": [
                    {"op": "init", "var": "temp", "value": 25.5},
                    {"op": "query", "var": "temp"},
                ],
            },
        )
        assert result["formatted"] == "25.5"

    @pytest.mark.asyncio
    async def test_formatted_none(self, expert: WeatherExpert) -> None:
        result = await expert.execute_operation("execute_trace", {"trace": []})
        assert result["formatted"] == ""

    @pytest.mark.asyncio
    @patch(
        "chuk_virtual_expert.mcp_expert.MCPExpert.execute_operation",
        new_callable=AsyncMock,
    )
    async def test_non_trace_delegates(self, mock_exec: AsyncMock, expert: WeatherExpert) -> None:
        mock_exec.return_value = {"query_type": "forecast", "latitude": 35.68}

        result = await expert.execute_operation("get_forecast", {"location": "tokyo"})

        assert result["query_type"] == "forecast"
        mock_exec.assert_called_once()


class TestBuildLocationParamsTyped:
    """Tests for _build_location_params_typed helper."""

    @pytest.fixture
    def expert(self) -> WeatherExpert:
        return WeatherExpert()

    def test_direct_location(self, expert: WeatherExpert) -> None:
        step = GetForecastStep(location="tokyo", var="weather")
        result = expert._build_location_params_typed(step, {})
        assert result["location"] == "tokyo"

    def test_direct_coords(self, expert: WeatherExpert) -> None:
        step = GetForecastStep(latitude=40.0, longitude=-74.0, var="weather")
        result = expert._build_location_params_typed(step, {})
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
        step = GetForecastStep(location_var="loc", var="weather")
        result = expert._build_location_params_typed(step, state)
        assert result["latitude"] == 47.37
        assert result["longitude"] == 8.54

    def test_location_var_missing_raises(self, expert: WeatherExpert) -> None:
        state: dict[str, Any] = {"loc": {"no_locations": True}}
        step = GetForecastStep(location_var="loc", var="weather")
        with pytest.raises(ValueError, match="Cannot extract coordinates"):
            expert._build_location_params_typed(step, state)


class TestWeatherTraceGenerator:
    """Tests for WeatherTraceGenerator."""

    @pytest.fixture
    def generator(self) -> WeatherTraceGenerator:
        return WeatherTraceGenerator(seed=42)

    def test_generate_get_forecast(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_get_forecast(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expert == "weather"
            assert ex.expected_operation == WeatherOperation.GET_FORECAST.value
            assert len(ex.trace) >= 2
            assert ex.query

    def test_generate_geocode(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_geocode(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expected_operation == WeatherOperation.GEOCODE.value

    def test_generate_get_historical(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_get_historical(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expected_operation == WeatherOperation.GET_HISTORICAL.value
            params = ex.expected_params
            assert "start_date" in params
            assert "end_date" in params

    def test_generate_get_air_quality(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_get_air_quality(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expected_operation == WeatherOperation.GET_AIR_QUALITY.value

    def test_generate_get_marine(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_get_marine(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.expected_operation == WeatherOperation.GET_MARINE.value

    def test_generate_multi_step(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_multi_step(5)
        assert len(examples) == 5
        for ex in examples:
            assert ex.multi_step is True
            assert len(ex.trace) == 3
            assert isinstance(ex.trace[0], GeocodeStep)
            assert isinstance(ex.trace[1], GetForecastStep)
            assert isinstance(ex.trace[2], QueryStep)

    def test_generate_all(self, generator: WeatherTraceGenerator) -> None:
        examples = generator.generate_all(n_per_type=3)
        # 6 types * 3 each = 18
        assert len(examples) == 18

    def test_reproducibility(self) -> None:
        gen1 = WeatherTraceGenerator(seed=123)
        gen2 = WeatherTraceGenerator(seed=123)
        r1 = gen1.generate_get_forecast(5)
        r2 = gen2.generate_get_forecast(5)
        assert r1 == r2

    def test_different_seeds(self) -> None:
        gen1 = WeatherTraceGenerator(seed=1)
        gen2 = WeatherTraceGenerator(seed=2)
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
            assert len(ex.query) > 10
            assert any(c.isalpha() for c in ex.query)

    def test_model_dump_produces_valid_format(self, generator: WeatherTraceGenerator) -> None:
        """Test that model_dump produces expected JSON structure."""
        examples = generator.generate_get_forecast(1)
        data = examples[0].model_dump()
        assert data["expert"] == "weather"
        assert isinstance(data["trace"], list)
        assert data["trace"][0]["op"] == "get_forecast"
        assert data["trace"][1]["op"] == "query"
