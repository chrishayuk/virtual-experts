"""Pytest configuration and fixtures for chuk-virtual-expert-weather tests."""

import pytest

from chuk_virtual_expert_weather import WeatherExpert


@pytest.fixture
def weather_expert() -> WeatherExpert:
    """Create a WeatherExpert instance for testing."""
    return WeatherExpert()
