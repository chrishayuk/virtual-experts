"""Tests for ExpertRegistry."""

from typing import Any, ClassVar

import pytest

from chuk_virtual_expert.expert import VirtualExpert
from chuk_virtual_expert.registry_v2 import ExpertRegistry, get_registry


class MockExpert(VirtualExpert):
    """Mock expert for testing registry."""

    name: ClassVar[str] = "mock"
    description: ClassVar[str] = "Mock expert"
    priority: ClassVar[int] = 5

    def get_operations(self) -> list[str]:
        return ["op1"]

    def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"result": "ok"}


class HighPriorityExpert(VirtualExpert):
    """High priority expert for testing ordering."""

    name: ClassVar[str] = "high"
    description: ClassVar[str] = "High priority"
    priority: ClassVar[int] = 10

    def get_operations(self) -> list[str]:
        return []

    def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
        return {}


class LowPriorityExpert(VirtualExpert):
    """Low priority expert for testing ordering."""

    name: ClassVar[str] = "low"
    description: ClassVar[str] = "Low priority"
    priority: ClassVar[int] = 1

    def get_operations(self) -> list[str]:
        return []

    def execute_operation(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
        return {}


class TestExpertRegistryCreation:
    """Tests for registry creation."""

    def test_create_empty_registry(self):
        registry = ExpertRegistry()
        assert len(registry) == 0

    def test_registry_is_empty_initially(self):
        registry = ExpertRegistry()
        assert registry.expert_names == []


class TestRegister:
    """Tests for register method."""

    def test_register_expert(self):
        registry = ExpertRegistry()
        expert = MockExpert()
        registry.register(expert)

        assert len(registry) == 1
        assert "mock" in registry

    def test_register_multiple(self):
        registry = ExpertRegistry()
        registry.register(MockExpert())
        registry.register(HighPriorityExpert())

        assert len(registry) == 2

    def test_register_duplicate_raises(self):
        registry = ExpertRegistry()
        registry.register(MockExpert())

        with pytest.raises(ValueError, match="already registered"):
            registry.register(MockExpert())


class TestUnregister:
    """Tests for unregister method."""

    def test_unregister_existing(self):
        registry = ExpertRegistry()
        registry.register(MockExpert())

        registry.unregister("mock")
        assert len(registry) == 0
        assert "mock" not in registry

    def test_unregister_nonexistent_raises(self):
        registry = ExpertRegistry()

        with pytest.raises(KeyError, match="No expert named"):
            registry.unregister("nonexistent")


class TestGet:
    """Tests for get method."""

    def test_get_existing(self):
        registry = ExpertRegistry()
        expert = MockExpert()
        registry.register(expert)

        result = registry.get("mock")
        assert result is expert

    def test_get_nonexistent_returns_none(self):
        registry = ExpertRegistry()

        result = registry.get("nonexistent")
        assert result is None


class TestGetAll:
    """Tests for get_all method."""

    def test_get_all_empty(self):
        registry = ExpertRegistry()
        result = registry.get_all()
        assert result == []

    def test_get_all_returns_list(self):
        registry = ExpertRegistry()
        registry.register(MockExpert())

        result = registry.get_all()
        assert isinstance(result, list)
        assert len(result) == 1

    def test_get_all_sorted_by_priority(self):
        registry = ExpertRegistry()
        registry.register(LowPriorityExpert())  # priority=1
        registry.register(HighPriorityExpert())  # priority=10
        registry.register(MockExpert())  # priority=5

        result = registry.get_all()
        priorities = [e.priority for e in result]

        assert priorities == [10, 5, 1]  # Descending order


class TestExpertNames:
    """Tests for expert_names property."""

    def test_expert_names_empty(self):
        registry = ExpertRegistry()
        assert registry.expert_names == []

    def test_expert_names_populated(self):
        registry = ExpertRegistry()
        registry.register(MockExpert())
        registry.register(HighPriorityExpert())

        names = registry.expert_names
        assert "mock" in names
        assert "high" in names


class TestItems:
    """Tests for items method."""

    def test_items_empty(self):
        registry = ExpertRegistry()
        items = list(registry.items())
        assert items == []

    def test_items_returns_pairs(self):
        registry = ExpertRegistry()
        expert = MockExpert()
        registry.register(expert)

        items = list(registry.items())
        assert len(items) == 1
        assert items[0][0] == "mock"
        assert items[0][1] is expert


class TestLen:
    """Tests for __len__ method."""

    def test_len_empty(self):
        registry = ExpertRegistry()
        assert len(registry) == 0

    def test_len_populated(self):
        registry = ExpertRegistry()
        registry.register(MockExpert())
        registry.register(HighPriorityExpert())

        assert len(registry) == 2


class TestContains:
    """Tests for __contains__ method."""

    def test_contains_true(self):
        registry = ExpertRegistry()
        registry.register(MockExpert())

        assert "mock" in registry

    def test_contains_false(self):
        registry = ExpertRegistry()

        assert "mock" not in registry


class TestRepr:
    """Tests for __repr__ method."""

    def test_repr_empty(self):
        registry = ExpertRegistry()
        repr_str = repr(registry)
        assert "ExpertRegistry" in repr_str

    def test_repr_with_experts(self):
        registry = ExpertRegistry()
        registry.register(MockExpert())

        repr_str = repr(registry)
        assert "mock" in repr_str


class TestGetRegistry:
    """Tests for get_registry global function."""

    def test_returns_registry(self):
        # Note: This modifies global state
        import chuk_virtual_expert.registry_v2 as module

        module._default_registry = None
        registry = get_registry()
        assert isinstance(registry, ExpertRegistry)

    def test_returns_same_instance(self):
        import chuk_virtual_expert.registry_v2 as module

        module._default_registry = None
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2
