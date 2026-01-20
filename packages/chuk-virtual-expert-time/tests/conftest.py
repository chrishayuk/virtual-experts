"""Pytest configuration and fixtures for chuk-virtual-expert-time tests."""

import pytest


@pytest.fixture
def time_expert():
    """Create a TimeExpert instance for testing."""
    from chuk_virtual_expert_time import TimeExpert

    return TimeExpert()
