"""Tests for environment registration."""

from __future__ import annotations

import copy

import pytest

from chuk_virtual_expert_mcts import (
    Environment,
    get_environment,
    register_environment,
    registered_environments,
)


class MinimalEnv:
    def get_actions(self, state):
        return [1] if state["n"] < 3 else []

    def step(self, state, action):
        return {"n": state["n"] + action}

    def is_done(self, state):
        return state["n"] >= 3

    def reward(self, state):
        return 1.0 if state["n"] == 3 else 0.0

    def initial(self, **kwargs):
        return {"n": 0}


class TestEnvironmentProtocol:
    def test_minimal_env_satisfies_protocol(self):
        env = MinimalEnv()
        assert isinstance(env, Environment)

    def test_lambda_class_not_protocol(self):
        # Object without all required methods
        class Bad:
            def get_actions(self, state):
                return []
        assert not isinstance(Bad(), Environment)


class TestRegistration:
    def test_register_and_get(self):
        register_environment("minimal", MinimalEnv())
        env = get_environment("minimal")
        assert isinstance(env, Environment)

    def test_registered_list(self):
        register_environment("list_test", MinimalEnv())
        assert "list_test" in registered_environments()

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown environment"):
            get_environment("does_not_exist_xyz")

    def test_register_non_protocol_raises(self):
        with pytest.raises(TypeError, match="Expected Environment"):
            register_environment("bad", "not an env")  # type: ignore
