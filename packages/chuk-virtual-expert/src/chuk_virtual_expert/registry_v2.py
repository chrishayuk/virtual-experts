"""
Clean registry for virtual experts.

Pydantic-native, type-safe, modular.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from pydantic import BaseModel, PrivateAttr

if TYPE_CHECKING:
    from chuk_virtual_expert.expert import VirtualExpert


class ExpertRegistry(BaseModel):
    """
    Registry for managing virtual experts.

    Provides registration, lookup, and iteration over experts.
    Each expert is stored by name and can be retrieved for dispatch.

    Example:
        registry = ExpertRegistry()
        registry.register(TimeExpert())
        registry.register(WeatherExpert())

        expert = registry.get("time")
        if expert:
            result = expert.execute(action)
    """

    model_config = {"arbitrary_types_allowed": True}

    # Private storage for experts
    _experts: dict[str, VirtualExpert] = PrivateAttr(default_factory=dict)

    def register(self, expert: VirtualExpert) -> None:
        """
        Register an expert.

        Args:
            expert: The expert instance to register

        Raises:
            ValueError: If an expert with the same name is already registered
        """
        if expert.name in self._experts:
            raise ValueError(f"Expert '{expert.name}' is already registered")
        self._experts[expert.name] = expert

    def unregister(self, name: str) -> None:
        """
        Unregister an expert by name.

        Args:
            name: The expert name to unregister

        Raises:
            KeyError: If no expert with that name exists
        """
        if name not in self._experts:
            raise KeyError(f"No expert named '{name}' is registered")
        del self._experts[name]

    def get(self, name: str) -> VirtualExpert | None:
        """
        Get an expert by name.

        Args:
            name: The expert name

        Returns:
            The expert instance, or None if not found
        """
        return self._experts.get(name)

    def get_all(self) -> list[VirtualExpert]:
        """
        Get all registered experts, sorted by priority (highest first).

        Returns:
            List of experts sorted by priority descending
        """
        return sorted(
            self._experts.values(),
            key=lambda e: e.priority,
            reverse=True,
        )

    @property
    def expert_names(self) -> list[str]:
        """List of registered expert names."""
        return list(self._experts.keys())

    def items(self) -> Iterator[tuple[str, VirtualExpert]]:
        """Iterate over (name, expert) pairs."""
        return iter(self._experts.items())

    def __len__(self) -> int:
        return len(self._experts)

    def __contains__(self, name: str) -> bool:
        return name in self._experts

    def __repr__(self) -> str:
        return f"ExpertRegistry(experts={self.expert_names})"


# Default global registry
_default_registry: ExpertRegistry | None = None


def get_registry() -> ExpertRegistry:
    """
    Get the default global registry.

    Creates the registry on first access.

    Returns:
        The default ExpertRegistry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = ExpertRegistry()
    return _default_registry
