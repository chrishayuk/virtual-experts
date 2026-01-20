"""Pytest configuration and fixtures for chuk-virtual-expert tests."""

import pytest


@pytest.fixture(autouse=True)
def reset_global_registry():
    """Reset the global registry before each test to avoid state leakage."""
    import chuk_virtual_expert.registry_v2 as module

    module._default_registry = None
    yield
    module._default_registry = None
