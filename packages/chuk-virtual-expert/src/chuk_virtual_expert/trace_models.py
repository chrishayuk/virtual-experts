"""
Typed trace step models for virtual expert framework.

Discriminated union of all trace step types using Pydantic.
Each step has an explicit `op` Literal field as the discriminator.
No magic strings - all operations use enums or Literal types.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class ComputeOp(str, Enum):
    """Arithmetic compute operations."""

    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    POW = "pow"
    SQRT = "sqrt"
    ABS = "abs"
    MIN = "min"
    MAX = "max"


# --- Base ---


class BaseTraceStep(BaseModel):
    """Base class for all typed trace steps."""

    op: str  # Overridden as Literal in each subclass


# --- Common Steps (used by all experts) ---


class InitStep(BaseTraceStep):
    """Initialize a variable with a value."""

    op: Literal["init"] = "init"
    var: str
    value: float | int | str | dict[str, Any] = Field(default=0)
    source: str | None = Field(default=None)  # "prev.result" for composition wiring


class GivenStep(BaseTraceStep):
    """Initialize multiple variables at once."""

    op: Literal["given"] = "given"
    values: dict[str, float]


class ComputeStep(BaseTraceStep):
    """Perform an arithmetic computation."""

    op: Literal["compute"] = "compute"
    compute_op: ComputeOp
    args: list[str | float | int]
    var: str | None = None


class FormulaStep(BaseTraceStep):
    """Informational formula annotation (no-op)."""

    op: Literal["formula"] = "formula"
    expression: str


class QueryStep(BaseTraceStep):
    """Specify which variable to return as the answer."""

    op: Literal["query"] = "query"
    var: str


class StateAssertStep(BaseTraceStep):
    """Assert expected variable values for verification."""

    op: Literal["state"] = "state"
    assertions: dict[str, float]


# --- Entity Tracking Steps ---


class TransferStep(BaseTraceStep):
    """Transfer amount from one entity to another."""

    op: Literal["transfer"] = "transfer"
    from_entity: str
    to_entity: str
    amount: str | float | int


class ConsumeStep(BaseTraceStep):
    """Consume/reduce an entity's value."""

    op: Literal["consume"] = "consume"
    entity: str
    amount: str | float | int


class AddEntityStep(BaseTraceStep):
    """Add to an entity's value."""

    op: Literal["add_entity"] = "add_entity"
    entity: str
    amount: str | float | int


# --- Percentage Steps ---


class PercentOffStep(BaseTraceStep):
    """Calculate X% off a base value."""

    op: Literal["percent_off"] = "percent_off"
    base: str | float | int
    rate: str | float | int
    var: str | None = None


class PercentIncreaseStep(BaseTraceStep):
    """Calculate X% increase on a base value."""

    op: Literal["percent_increase"] = "percent_increase"
    base: str | float | int
    rate: str | float | int
    var: str | None = None


class PercentOfStep(BaseTraceStep):
    """Calculate X% of a base value."""

    op: Literal["percent_of"] = "percent_of"
    base: str | float | int
    rate: str | float | int
    var: str | None = None


# --- Comparison Steps ---


class CompareStep(BaseTraceStep):
    """Compare two values using a compute operation."""

    op: Literal["compare"] = "compare"
    compute_op: ComputeOp
    args: list[str | float | int]
    var: str | None = None


# --- Weather Steps ---


class GeocodeStep(BaseTraceStep):
    """Geocode a location name to coordinates."""

    op: Literal["geocode"] = "geocode"
    name: str
    var: str = "result"


class GetForecastStep(BaseTraceStep):
    """Get weather forecast for a location."""

    op: Literal["get_forecast"] = "get_forecast"
    location: str | None = None
    location_var: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    forecast_days: int = 3
    unit: str | None = None
    temperature_unit: str | None = None
    var: str = "result"


class GetHistoricalStep(BaseTraceStep):
    """Get historical weather data."""

    op: Literal["get_historical"] = "get_historical"
    location: str | None = None
    location_var: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    start_date: str = ""
    end_date: str = ""
    var: str = "result"


class GetAirQualityStep(BaseTraceStep):
    """Get air quality data for a location."""

    op: Literal["get_air_quality"] = "get_air_quality"
    location: str | None = None
    location_var: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    var: str = "result"


class GetMarineStep(BaseTraceStep):
    """Get marine forecast for a location."""

    op: Literal["get_marine"] = "get_marine"
    location: str | None = None
    location_var: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    forecast_days: int = 3
    var: str = "result"


class InterpretCodeStep(BaseTraceStep):
    """Interpret a weather code."""

    op: Literal["interpret_code"] = "interpret_code"
    weather_code: int = 0
    var: str = "result"


# --- Time Steps ---


class GetTimeStep(BaseTraceStep):
    """Get current time in a timezone."""

    op: Literal["get_time"] = "get_time"
    timezone: str = "UTC"
    var: str = "result"


class ConvertTimeStep(BaseTraceStep):
    """Convert time between timezones."""

    op: Literal["convert_time"] = "convert_time"
    time: str = ""
    time_var: str | None = None
    from_timezone: str = "UTC"
    to_timezone: str = "UTC"
    var: str = "result"


class GetTimezoneInfoStep(BaseTraceStep):
    """Get timezone information for a location."""

    op: Literal["get_timezone_info"] = "get_timezone_info"
    location: str = ""
    var: str = "result"


# --- Discriminated Union ---

TraceStep = Annotated[
    InitStep
    | GivenStep
    | ComputeStep
    | FormulaStep
    | QueryStep
    | StateAssertStep
    | TransferStep
    | ConsumeStep
    | AddEntityStep
    | PercentOffStep
    | PercentIncreaseStep
    | PercentOfStep
    | CompareStep
    | GeocodeStep
    | GetForecastStep
    | GetHistoricalStep
    | GetAirQualityStep
    | GetMarineStep
    | InterpretCodeStep
    | GetTimeStep
    | ConvertTimeStep
    | GetTimezoneInfoStep,
    Field(discriminator="op"),
]

# All step types for export
ALL_STEP_TYPES = (
    InitStep,
    GivenStep,
    ComputeStep,
    FormulaStep,
    QueryStep,
    StateAssertStep,
    TransferStep,
    ConsumeStep,
    AddEntityStep,
    PercentOffStep,
    PercentIncreaseStep,
    PercentOfStep,
    CompareStep,
    GeocodeStep,
    GetForecastStep,
    GetHistoricalStep,
    GetAirQualityStep,
    GetMarineStep,
    InterpretCodeStep,
    GetTimeStep,
    ConvertTimeStep,
    GetTimezoneInfoStep,
)
