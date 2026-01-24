"""Shared test fixtures — provides a simple counting environment."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from chuk_virtual_expert_mcts import register_environment


class CountingEnv:
    """Simple environment: increment a counter toward a target.

    Actions: 1, 2, 3 (amount to add)
    Done when: value >= target or moves exhausted
    Reward: 1.0 if value == target, else proportional closeness
    """

    def get_actions(self, state: dict[str, Any]) -> list[int]:
        if state["moves_left"] <= 0:
            return []
        return [a for a in [1, 2, 3] if state["value"] + a <= state["target"]]

    def step(self, state: dict[str, Any], action: int) -> dict[str, Any]:
        s = copy.deepcopy(state)
        s["value"] += action
        s["moves_left"] -= 1
        return s

    def is_done(self, state: dict[str, Any]) -> bool:
        return state["moves_left"] <= 0 or state["value"] >= state["target"]

    def reward(self, state: dict[str, Any]) -> float:
        if state["value"] == state["target"]:
            return 1.0
        return max(0.0, 1.0 - abs(state["value"] - state["target"]) / state["target"])

    def initial(self, target: int = 10, moves: int = 5, **_: Any) -> dict[str, Any]:
        return {"value": 0, "target": int(target), "moves_left": int(moves)}


@pytest.fixture(autouse=True)
def register_counting_env():
    """Register counting env for all tests."""
    register_environment("counting", CountingEnv())
    yield
