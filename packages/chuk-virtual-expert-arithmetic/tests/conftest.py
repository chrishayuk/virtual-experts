"""Pytest configuration and fixtures for chuk-virtual-expert-arithmetic tests."""

import pytest

from chuk_virtual_expert_arithmetic import (
    ArithmeticExpert,
    ComparisonExpert,
    EntityTrackExpert,
    PercentageExpert,
    RateEquationExpert,
)


@pytest.fixture
def arithmetic_expert() -> ArithmeticExpert:
    """Create an ArithmeticExpert instance for testing."""
    return ArithmeticExpert()


@pytest.fixture
def entity_track_expert() -> EntityTrackExpert:
    """Create an EntityTrackExpert instance for testing."""
    return EntityTrackExpert()


@pytest.fixture
def percentage_expert() -> PercentageExpert:
    """Create a PercentageExpert instance for testing."""
    return PercentageExpert()


@pytest.fixture
def rate_equation_expert() -> RateEquationExpert:
    """Create a RateEquationExpert instance for testing."""
    return RateEquationExpert()


@pytest.fixture
def comparison_expert() -> ComparisonExpert:
    """Create a ComparisonExpert instance for testing."""
    return ComparisonExpert()
