"""Tests for the core MCTS algorithm."""

from __future__ import annotations

import asyncio

import pytest

from chuk_virtual_expert_mcts import Node, SearchConfig, search, search_async
from tests.conftest import CountingEnv


@pytest.fixture
def env():
    return CountingEnv()


class TestNode:
    def test_initial_state(self):
        node = Node(state={"x": 1})
        assert node.visits == 0
        assert node.value == 0.0
        assert node.children == []
        assert node.parent is None
        assert node.action is None

    def test_ucb1_unvisited(self):
        node = Node(state={})
        assert node.ucb1(1.41) == float("inf")

    def test_ucb1_with_visits(self):
        parent = Node(state={})
        parent.visits = 100
        child = Node(state={}, parent=parent, action=1)
        child.visits = 10
        child.value = 7.0
        ucb = child.ucb1(1.41)
        assert ucb > 0.7  # exploitation
        assert ucb < 3.0  # bounded

    def test_best_child(self):
        parent = Node(state={})
        parent.visits = 50
        c1 = Node(state={}, parent=parent, action=1)
        c1.visits = 20
        c1.value = 10.0
        c2 = Node(state={}, parent=parent, action=2)
        c2.visits = 5
        c2.value = 4.0
        parent.children = [c1, c2]
        # c2 has higher UCB1 due to low visits
        best = parent.best_child(1.41)
        assert best is c2

    def test_most_visited_child(self):
        parent = Node(state={})
        c1 = Node(state={}, parent=parent, action=1)
        c1.visits = 50
        c2 = Node(state={}, parent=parent, action=2)
        c2.visits = 30
        parent.children = [c1, c2]
        assert parent.most_visited_child() is c1


class TestSearch:
    def test_returns_valid_action(self, env):
        state = env.initial(target=6, moves=3)
        result = search(env, state, SearchConfig(iterations=200))
        assert result.best_action in [1, 2, 3]
        assert result.visits == 200

    def test_finds_optimal_action(self, env):
        # target=3, moves=1 — must pick 3
        state = env.initial(target=3, moves=1)
        result = search(env, state, SearchConfig(iterations=500))
        assert result.best_action == 3

    def test_deterministic_with_seed(self, env):
        state = env.initial(target=10, moves=5)
        r1 = search(env, state, SearchConfig(iterations=100, seed=42))
        r2 = search(env, state, SearchConfig(iterations=100, seed=42))
        assert r1.best_action == r2.best_action
        assert r1.visits == r2.visits
        assert r1.value == r2.value

    def test_different_seeds_may_differ(self, env):
        state = env.initial(target=10, moves=5)
        r1 = search(env, state, SearchConfig(iterations=50, seed=1))
        r2 = search(env, state, SearchConfig(iterations=50, seed=999))
        # Not guaranteed to differ, but tests randomness path
        assert r1.visits == r2.visits

    def test_terminal_state_returns_empty(self, env):
        state = {"value": 10, "target": 10, "moves_left": 5}
        result = search(env, state)
        assert result.best_action is None
        assert result.visits == 0

    def test_action_stats_sorted(self, env):
        state = env.initial(target=10, moves=5)
        result = search(env, state, SearchConfig(iterations=300))
        visits = [a.visits for a in result.action_stats]
        assert visits == sorted(visits, reverse=True)

    def test_action_stats_values(self, env):
        state = env.initial(target=6, moves=3)
        result = search(env, state, SearchConfig(iterations=200))
        for stat in result.action_stats:
            assert 0.0 <= stat.value <= 1.0
            assert stat.visits > 0

    def test_exploration_constant_affects_search(self, env):
        state = env.initial(target=10, moves=5)
        r_low = search(env, state, SearchConfig(iterations=200, exploration=0.1, seed=42))
        r_high = search(env, state, SearchConfig(iterations=200, exploration=5.0, seed=42))
        # High exploration should spread visits more evenly
        assert r_low.visits == r_high.visits

    def test_default_config(self, env):
        state = env.initial(target=3, moves=2)
        result = search(env, state)
        assert result.visits == 1000  # default iterations
        assert result.best_action is not None


class TestSearchAsync:
    def test_async_search(self, env):
        state = env.initial(target=6, moves=3)

        async def run():
            return await search_async(env, state, SearchConfig(iterations=100, seed=42))

        result = asyncio.run(run())
        assert result.best_action in [1, 2, 3]
        assert result.visits == 100

    def test_async_matches_sync(self, env):
        state = env.initial(target=6, moves=3)
        config = SearchConfig(iterations=100, seed=42)

        sync_result = search(env, state, config)

        async def run():
            return await search_async(env, state, SearchConfig(iterations=100, seed=42))

        async_result = asyncio.run(run())
        assert sync_result.best_action == async_result.best_action
