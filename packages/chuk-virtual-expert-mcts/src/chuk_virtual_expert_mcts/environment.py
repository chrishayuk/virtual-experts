"""Environment protocol for MCTS search."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Environment(Protocol):
    """Protocol for environments searchable by MCTS.

    Implementations must provide:
        get_actions: Available actions from a state
        step: Apply action, return new state (must not mutate input)
        is_done: Whether state is terminal
        reward: Terminal state reward (0.0-1.0)

    Optional:
        initial: Create initial state from kwargs
        from_str: Parse state from string representation
    """

    def get_actions(self, state: Any) -> list[Any]:
        """Return available actions from this state."""
        ...

    def step(self, state: Any, action: Any) -> Any:
        """Apply action to state, return new state."""
        ...

    def is_done(self, state: Any) -> bool:
        """Return True if state is terminal."""
        ...

    def reward(self, state: Any) -> float:
        """Return reward for terminal state (0.0-1.0)."""
        ...


_REGISTRY: dict[str, Environment] = {}


def register_environment(name: str, env: Environment) -> None:
    """Register an environment for MCTS search."""
    if not isinstance(env, Environment):
        raise TypeError(f"Expected Environment protocol, got {type(env).__name__}")
    _REGISTRY[name] = env


def get_environment(name: str) -> Environment:
    """Get a registered environment by name."""
    if name not in _REGISTRY:
        raise KeyError(f"Unknown environment: {name!r}. Registered: {list(_REGISTRY.keys())}")
    return _REGISTRY[name]


def registered_environments() -> list[str]:
    """List registered environment names."""
    return list(_REGISTRY.keys())
