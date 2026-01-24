"""Pytest configuration and fixtures for chuk-virtual-expert-time tests."""

import pytest

from chuk_virtual_expert_time import TimeExpert


@pytest.fixture
def time_expert() -> TimeExpert:
    """Create a TimeExpert instance for testing."""
    return TimeExpert()
