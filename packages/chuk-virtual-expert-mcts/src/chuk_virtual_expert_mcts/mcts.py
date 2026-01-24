"""Pure MCTS algorithm — Node and tree search.

Domain-agnostic. Operates on any Environment protocol implementation.
"""

from __future__ import annotations

import asyncio
import math
import random
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from chuk_virtual_expert_mcts.environment import Environment
from chuk_virtual_expert_mcts.models import ActionStat, SearchConfig, SearchResult


class Node:
    """A node in the MCTS search tree."""

    __slots__ = ("state", "parent", "action", "children", "visits", "value", "untried")

    def __init__(self, state: Any, parent: Node | None = None, action: Any = None) -> None:
        self.state = state
        self.parent = parent
        self.action = action
        self.children: list[Node] = []
        self.visits: int = 0
        self.value: float = 0.0
        self.untried: list[Any] = []

    def ucb1(self, exploration: float) -> float:
        if self.visits == 0:
            return float("inf")
        assert self.parent is not None
        return (self.value / self.visits) + exploration * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )

    def best_child(self, exploration: float) -> Node:
        return max(self.children, key=lambda c: c.ucb1(exploration))

    def most_visited_child(self) -> Node:
        return max(self.children, key=lambda c: c.visits)


_EXECUTOR = ThreadPoolExecutor(max_workers=2)


def search(env: Environment, state: Any, config: SearchConfig | None = None) -> SearchResult:
    """Run MCTS from the given state.

    Args:
        env: Environment providing actions, transitions, terminal check, reward
        state: Root state
        config: Search configuration (iterations, exploration, seed)

    Returns:
        SearchResult with best_action, visits, value, action_stats
    """
    if config is None:
        config = SearchConfig()

    rng = random.Random(config.seed)

    root = Node(state=state)
    root.untried = env.get_actions(state) if not env.is_done(state) else []

    if not root.untried:
        return SearchResult()

    for _ in range(config.iterations):
        node = root

        # SELECT
        while not node.untried and node.children:
            node = node.best_child(config.exploration)

        # EXPAND
        if node.untried:
            action = rng.choice(node.untried)
            node.untried.remove(action)
            new_state = env.step(node.state, action)
            child = Node(state=new_state, parent=node, action=action)
            child.untried = env.get_actions(new_state) if not env.is_done(new_state) else []
            node.children.append(child)
            node = child

        # ROLLOUT
        rollout_state = node.state
        while not env.is_done(rollout_state):
            actions = env.get_actions(rollout_state)
            if not actions:
                break
            rollout_state = env.step(rollout_state, rng.choice(actions))

        # BACKPROPAGATE
        r = env.reward(rollout_state)
        current: Node | None = node
        while current is not None:
            current.visits += 1
            current.value += r
            current = current.parent

    best = root.most_visited_child()
    action_stats = sorted(
        [
            ActionStat(
                action=c.action,
                visits=c.visits,
                value=c.value / c.visits if c.visits else 0.0,
            )
            for c in root.children
        ],
        key=lambda x: x.visits,
        reverse=True,
    )

    return SearchResult(
        best_action=best.action,
        visits=root.visits,
        value=best.value / best.visits if best.visits else 0.0,
        action_stats=action_stats,
    )


async def search_async(
    env: Environment, state: Any, config: SearchConfig | None = None
) -> SearchResult:
    """Async version — runs search in thread pool to avoid blocking."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_EXECUTOR, search, env, state, config)
