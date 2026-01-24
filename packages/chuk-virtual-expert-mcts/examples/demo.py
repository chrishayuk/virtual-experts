"""Demo: Using MctsExpert with a simple counting environment."""

from __future__ import annotations

import asyncio
import copy
from typing import Any

from chuk_virtual_expert.trace_models import QueryStep

from chuk_virtual_expert_mcts import (
    MctsExpert,
    register_environment,
    search_async,
    SearchConfig,
)
from chuk_virtual_expert_mcts.models import (
    ApplyStep,
    EvaluateStep,
    InitSearchStep,
    SearchStep,
)


# Define a simple environment
class CountingEnv:
    """Reach target by adding 1, 2, or 3 each step."""

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
        return 1.0 if state["value"] == state["target"] else 0.0

    def initial(self, target: int = 10, moves: int = 5, **_: Any) -> dict[str, Any]:
        return {"value": 0, "target": int(target), "moves_left": int(moves)}


async def main() -> None:
    # Register environment
    register_environment("counting", CountingEnv())

    expert = MctsExpert()

    # Simple search
    print("=== Search for best action ===")
    result = await expert.execute_trace(
        [
            InitSearchStep(env="counting", params={"target": 6, "moves": 3}),
            SearchStep(iterations=1000, var="best", seed=42),
            QueryStep(var="best"),
        ]
    )
    print(f"  Best action: {result.answer}")
    print(f"  Stats: {result.state.get('_search_stats', {})}")

    # Multi-step search
    print("\n=== Multi-step search and apply ===")
    result = await expert.execute_trace(
        [
            InitSearchStep(env="counting", params={"target": 9, "moves": 4}),
            SearchStep(iterations=500, var="a1", seed=1),
            ApplyStep(action_var="a1"),
            SearchStep(iterations=500, var="a2", seed=2),
            ApplyStep(action_var="a2"),
            SearchStep(iterations=500, var="a3", seed=3),
            ApplyStep(action_var="a3"),
            EvaluateStep(var="final_value"),
            QueryStep(var="final_value"),
        ]
    )
    print(
        f"  Actions: a1={result.state['a1']}, a2={result.state['a2']}, a3={result.state['a3']}"
    )
    print(f"  Final value: {result.state['_state']['value']}")
    print(f"  Reward: {result.answer}")

    # Evaluate a position
    print("\n=== Evaluate position ===")
    result = await expert.execute_trace(
        [
            InitSearchStep(env="counting", params={"target": 6, "moves": 2}),
            EvaluateStep(iterations=1000, var="value"),
            QueryStep(var="value"),
        ]
    )
    print(f"  Value estimate: {result.answer:.3f}")

    # Using async search directly
    print("\n=== Async search (direct) ===")
    env = CountingEnv()
    state = env.initial(target=6, moves=3)
    search_result = await search_async(
        env, state, SearchConfig(iterations=500, seed=42)
    )
    print(f"  Best action: {search_result.best_action}")
    print(f"  Value: {search_result.value:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
