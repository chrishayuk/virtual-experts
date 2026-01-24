"""Demo: Using MctsExpert with a simple counting environment."""

from __future__ import annotations

import copy
from typing import Any

from chuk_virtual_expert_mcts import MctsExpert, register_environment, MctsOperation


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


def main():
    # Register environment
    register_environment("counting", CountingEnv())

    expert = MctsExpert()

    # Simple search
    print("=== Search for best action ===")
    result = expert.execute_trace([
        {MctsOperation.INIT_SEARCH.value: {"env": "counting", "target": 6, "moves": 3}},
        {MctsOperation.SEARCH.value: {"iterations": 1000, "var": "best", "seed": 42}},
        {"query": "best"},
    ])
    print(f"  Best action: {result.answer}")
    print(f"  Stats: {result.state.get('_search_stats', {})}")

    # Multi-step search
    print("\n=== Multi-step search and apply ===")
    result = expert.execute_trace([
        {MctsOperation.INIT_SEARCH.value: {"env": "counting", "target": 9, "moves": 4}},
        {MctsOperation.SEARCH.value: {"iterations": 500, "var": "a1", "seed": 1}},
        {MctsOperation.APPLY.value: {"action_var": "a1"}},
        {MctsOperation.SEARCH.value: {"iterations": 500, "var": "a2", "seed": 2}},
        {MctsOperation.APPLY.value: {"action_var": "a2"}},
        {MctsOperation.SEARCH.value: {"iterations": 500, "var": "a3", "seed": 3}},
        {MctsOperation.APPLY.value: {"action_var": "a3"}},
        {MctsOperation.EVALUATE.value: {"var": "final_value"}},
        {"query": "final_value"},
    ])
    print(f"  Actions: a1={result.state['a1']}, a2={result.state['a2']}, a3={result.state['a3']}")
    print(f"  Final value: {result.state['_state']['value']}")
    print(f"  Reward: {result.answer}")

    # Evaluate a position
    print("\n=== Evaluate position ===")
    result = expert.execute_trace([
        {MctsOperation.INIT_SEARCH.value: {"env": "counting", "target": 6, "moves": 2}},
        {MctsOperation.EVALUATE.value: {"iterations": 1000, "var": "value"}},
        {"query": "value"},
    ])
    print(f"  Value estimate: {result.answer:.3f}")

    # Using async
    print("\n=== Async search ===")
    import asyncio
    from chuk_virtual_expert_mcts import search_async, SearchConfig

    async def async_demo():
        env = CountingEnv()
        state = env.initial(target=6, moves=3)
        result = await search_async(env, state, SearchConfig(iterations=500, seed=42))
        print(f"  Best action: {result.best_action}")
        print(f"  Value: {result.value:.3f}")

    asyncio.run(async_demo())


if __name__ == "__main__":
    main()
