"""
Weather trace generator for synthetic training data.

Generates structured TraceExample models for all weather operations,
useful for training and evaluation.
"""

from __future__ import annotations

import random

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import (
    GeocodeStep,
    GetAirQualityStep,
    GetForecastStep,
    GetHistoricalStep,
    GetMarineStep,
    QueryStep,
)

from chuk_virtual_expert_weather.expert import LOCATION_ALIASES, WeatherOperation

# Cities with coordinates for generation
CITY_COORDS: dict[str, tuple[float, float]] = {
    city: (coords["latitude"], coords["longitude"])
    for city, coords in LOCATION_ALIASES.items()
    if len(city) > 2  # Skip abbreviations like "la", "sf", "nyc"
}

# Query templates per operation
_FORECAST_QUERIES: list[str] = [
    "What's the weather in {city}?",
    "Weather forecast for {city}",
    "Will it rain in {city} today?",
    "Temperature in {city} this week",
    "Current conditions in {city}",
    "{city} weather forecast",
    "How's the weather in {city}?",
    "Is it sunny in {city}?",
]

_GEOCODE_QUERIES: list[str] = [
    "Where is {city}?",
    "Find coordinates for {city}",
    "Geocode {city}",
    "Location of {city}",
    "What are the coordinates of {city}?",
]

_HISTORICAL_QUERIES: list[str] = [
    "Historical weather in {city} for {start_date} to {end_date}",
    "What was the weather in {city} on {start_date}?",
    "Past weather data for {city}",
    "Temperature history for {city}",
]

_AIR_QUALITY_QUERIES: list[str] = [
    "Air quality in {city}",
    "Pollution levels in {city}",
    "Is the air clean in {city}?",
    "AQI for {city}",
    "Air pollution in {city} today",
]

_MARINE_QUERIES: list[str] = [
    "Ocean conditions near {city}",
    "Marine forecast for {city}",
    "Wave height near {city}",
    "Sea conditions at {city}",
    "Surf forecast for {city}",
]

# Sample date ranges for historical queries
_DATE_RANGES: list[tuple[str, str]] = [
    ("2024-01-01", "2024-01-07"),
    ("2024-03-15", "2024-03-21"),
    ("2024-06-01", "2024-06-07"),
    ("2024-08-10", "2024-08-16"),
    ("2024-11-01", "2024-11-07"),
    ("2023-12-20", "2023-12-26"),
    ("2023-07-01", "2023-07-07"),
    ("2024-09-01", "2024-09-30"),
]


class WeatherTraceGenerator:
    """
    Generates synthetic weather trace examples for training.

    Uses seeded randomness for reproducibility.
    """

    def __init__(self, seed: int = 42) -> None:
        """Initialize with a random seed for reproducibility."""
        self._rng = random.Random(seed)

    def _pick_cities(self, n: int) -> list[str]:
        """Pick n random cities from the alias list."""
        cities = list(CITY_COORDS.keys())
        return [self._rng.choice(cities) for _ in range(n)]

    def generate_get_forecast(self, n: int = 10) -> list[TraceExample]:
        """Generate n get_forecast trace examples."""
        examples: list[TraceExample] = []
        cities = self._pick_cities(n)

        for city in cities:
            query = self._rng.choice(_FORECAST_QUERIES).format(city=city.title())
            lat, lon = CITY_COORDS[city]
            forecast_days = self._rng.choice([1, 3, 5, 7])

            examples.append(
                TraceExample(
                    expert="weather",
                    query=query,
                    trace=[
                        GetForecastStep(
                            location=city,
                            forecast_days=forecast_days,
                            var="weather",
                        ),
                        QueryStep(var="weather"),
                    ],
                    expected_operation=WeatherOperation.GET_FORECAST.value,
                    expected_params={
                        "latitude": lat,
                        "longitude": lon,
                        "forecast_days": forecast_days,
                    },
                )
            )

        return examples

    def generate_geocode(self, n: int = 10) -> list[TraceExample]:
        """Generate n geocode trace examples."""
        examples: list[TraceExample] = []
        cities = self._pick_cities(n)

        for city in cities:
            query = self._rng.choice(_GEOCODE_QUERIES).format(city=city.title())

            examples.append(
                TraceExample(
                    expert="weather",
                    query=query,
                    trace=[
                        GeocodeStep(name=city.title(), var="location"),
                        QueryStep(var="location"),
                    ],
                    expected_operation=WeatherOperation.GEOCODE.value,
                    expected_params={"name": city.title()},
                )
            )

        return examples

    def generate_get_historical(self, n: int = 10) -> list[TraceExample]:
        """Generate n get_historical trace examples."""
        examples: list[TraceExample] = []
        cities = self._pick_cities(n)

        for city in cities:
            start, end = self._rng.choice(_DATE_RANGES)
            query = self._rng.choice(_HISTORICAL_QUERIES).format(
                city=city.title(), start_date=start, end_date=end
            )
            lat, lon = CITY_COORDS[city]

            examples.append(
                TraceExample(
                    expert="weather",
                    query=query,
                    trace=[
                        GetHistoricalStep(
                            location=city,
                            start_date=start,
                            end_date=end,
                            var="history",
                        ),
                        QueryStep(var="history"),
                    ],
                    expected_operation=WeatherOperation.GET_HISTORICAL.value,
                    expected_params={
                        "latitude": lat,
                        "longitude": lon,
                        "start_date": start,
                        "end_date": end,
                    },
                )
            )

        return examples

    def generate_get_air_quality(self, n: int = 10) -> list[TraceExample]:
        """Generate n get_air_quality trace examples."""
        examples: list[TraceExample] = []
        cities = self._pick_cities(n)

        for city in cities:
            query = self._rng.choice(_AIR_QUALITY_QUERIES).format(city=city.title())
            lat, lon = CITY_COORDS[city]

            examples.append(
                TraceExample(
                    expert="weather",
                    query=query,
                    trace=[
                        GetAirQualityStep(location=city, var="aqi"),
                        QueryStep(var="aqi"),
                    ],
                    expected_operation=WeatherOperation.GET_AIR_QUALITY.value,
                    expected_params={"latitude": lat, "longitude": lon},
                )
            )

        return examples

    def generate_get_marine(self, n: int = 10) -> list[TraceExample]:
        """Generate n get_marine trace examples."""
        examples: list[TraceExample] = []
        # Prefer coastal cities
        coastal = ["miami", "sydney", "tokyo", "los angeles", "seattle", "hong kong", "mumbai"]
        cities = [self._rng.choice(coastal) for _ in range(n)]

        for city in cities:
            query = self._rng.choice(_MARINE_QUERIES).format(city=city.title())
            lat, lon = CITY_COORDS[city]
            forecast_days = self._rng.choice([3, 5, 7])

            examples.append(
                TraceExample(
                    expert="weather",
                    query=query,
                    trace=[
                        GetMarineStep(
                            location=city,
                            forecast_days=forecast_days,
                            var="marine",
                        ),
                        QueryStep(var="marine"),
                    ],
                    expected_operation=WeatherOperation.GET_MARINE.value,
                    expected_params={
                        "latitude": lat,
                        "longitude": lon,
                        "forecast_days": forecast_days,
                    },
                )
            )

        return examples

    def generate_multi_step(self, n: int = 10) -> list[TraceExample]:
        """Generate n multi-step traces (geocode then forecast)."""
        examples: list[TraceExample] = []
        # Use city names not in aliases to force geocoding
        unknown_cities = [
            "Zurich",
            "Helsinki",
            "Osaka",
            "Melbourne",
            "Vancouver",
            "Prague",
            "Vienna",
            "Stockholm",
            "Copenhagen",
            "Lisbon",
            "Warsaw",
            "Budapest",
            "Athens",
            "Dublin",
            "Brussels",
        ]

        for _ in range(n):
            city = self._rng.choice(unknown_cities)
            forecast_days = self._rng.choice([3, 5, 7])

            examples.append(
                TraceExample(
                    expert="weather",
                    query=f"Weather forecast for {city}",
                    trace=[
                        GeocodeStep(name=city, var="loc"),
                        GetForecastStep(
                            location_var="loc",
                            forecast_days=forecast_days,
                            var="weather",
                        ),
                        QueryStep(var="weather"),
                    ],
                    expected_operation="execute_trace",
                    multi_step=True,
                )
            )

        return examples

    def generate_all(self, n_per_type: int = 10) -> list[TraceExample]:
        """Generate examples for all operation types, shuffled."""
        all_examples: list[TraceExample] = []
        all_examples.extend(self.generate_get_forecast(n_per_type))
        all_examples.extend(self.generate_geocode(n_per_type))
        all_examples.extend(self.generate_get_historical(n_per_type))
        all_examples.extend(self.generate_get_air_quality(n_per_type))
        all_examples.extend(self.generate_get_marine(n_per_type))
        all_examples.extend(self.generate_multi_step(n_per_type))
        self._rng.shuffle(all_examples)
        return all_examples

    @staticmethod
    def get_location_aliases() -> dict[str, dict[str, float]]:
        """Return the LOCATION_ALIASES dictionary."""
        return LOCATION_ALIASES
