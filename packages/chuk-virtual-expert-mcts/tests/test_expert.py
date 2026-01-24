"""Tests for MctsExpert trace execution."""

from __future__ import annotations

import pytest

from chuk_virtual_expert_mcts import MctsExpert, MctsOperation


class TestCanHandle:
    def setup_method(self):
        self.expert = MctsExpert()

    def test_mcts_keyword(self):
        assert self.expert.can_handle("Use MCTS to search")

    def test_monte_carlo_keyword(self):
        assert self.expert.can_handle("Run Monte Carlo tree search")

    def test_registered_env_name(self):
        assert self.expert.can_handle("Solve the counting problem")

    def test_rejects_unrelated(self):
        assert not self.expert.can_handle("What is the weather?")

    def test_rejects_math(self):
        assert not self.expert.can_handle("What is 5 + 3?")


class TestInitSearch:
    def setup_method(self):
        self.expert = MctsExpert()

    def test_basic_init(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 5, "moves": 3}},
        ])
        assert result.success
        assert result.state["_env"] == "counting"
        assert result.state["_state"]["target"] == 5
        assert result.state["_state"]["moves_left"] == 3

    def test_default_params(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting"}},
        ])
        assert result.success
        assert result.state["_state"]["target"] == 10  # default

    def test_unknown_env_fails(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "nonexistent"}},
        ])
        assert not result.success
        assert "Unknown environment" in result.error

    def test_unknown_operation_fails(self):
        result = self.expert.execute_trace([
            {"bogus_op": {"foo": "bar"}},
        ])
        assert not result.success


class TestSearch:
    def setup_method(self):
        self.expert = MctsExpert()

    def test_produces_action(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 6, "moves": 3}},
            {"search": {"iterations": 200, "var": "action", "seed": 42}},
            {"query": "action"},
        ])
        assert result.success
        assert result.answer in [1, 2, 3]

    def test_without_init_fails(self):
        result = self.expert.execute_trace([
            {"search": {"iterations": 100}},
        ])
        assert not result.success
        assert "No environment" in result.error

    def test_stores_stats(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 6, "moves": 3}},
            {"search": {"iterations": 100, "seed": 1}},
        ])
        assert result.success
        stats = result.state["_search_stats"]
        assert stats["visits"] == 100
        assert "top_actions" in stats

    def test_default_var_name(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 3, "moves": 1}},
            {"search": {"iterations": 100, "seed": 1}},
            {"query": "best_action"},
        ])
        assert result.success
        assert result.answer == 3

    def test_custom_exploration(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 6, "moves": 3}},
            {"search": {"iterations": 200, "exploration": 0.5, "var": "a", "seed": 1}},
            {"query": "a"},
        ])
        assert result.success


class TestApply:
    def setup_method(self):
        self.expert = MctsExpert()

    def test_direct_action(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 10, "moves": 5}},
            {"apply": {"action": 3}},
        ])
        assert result.success
        assert result.state["_state"]["value"] == 3
        assert result.state["_state"]["moves_left"] == 4

    def test_from_var(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 6, "moves": 3}},
            {"search": {"iterations": 100, "var": "a", "seed": 42}},
            {"apply": {"action_var": "a"}},
        ])
        assert result.success
        assert result.state["_state"]["value"] > 0

    def test_illegal_action_fails(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 10, "moves": 5}},
            {"apply": {"action": 3}},
            {"apply": {"action": 3}},
            {"apply": {"action": 3}},
            {"apply": {"action": 3}},  # value=12 > target
        ])
        assert not result.success
        assert "Illegal" in result.error

    def test_missing_var_fails(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 10, "moves": 5}},
            {"apply": {"action_var": "nonexistent"}},
        ])
        assert not result.success
        assert "not found" in result.error

    def test_no_action_param_fails(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 10, "moves": 5}},
            {"apply": {}},
        ])
        assert not result.success
        assert "requires" in result.error


class TestEvaluate:
    def setup_method(self):
        self.expert = MctsExpert()

    def test_non_terminal(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 3, "moves": 1}},
            {"evaluate": {"iterations": 200, "var": "v", "seed": 1}},
            {"query": "v"},
        ])
        assert result.success
        assert isinstance(result.answer, (int, float))
        assert 0.0 <= float(result.answer) <= 1.0

    def test_terminal_exact(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 3, "moves": 5}},
            {"apply": {"action": 3}},
            {"evaluate": {"var": "v"}},
            {"query": "v"},
        ])
        assert result.success
        assert float(result.answer) == 1.0

    def test_default_var_name(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 3, "moves": 1}},
            {"evaluate": {"iterations": 50, "seed": 1}},
            {"query": "value"},
        ])
        assert result.success


class TestFullTraces:
    def setup_method(self):
        self.expert = MctsExpert()

    def test_search_apply_evaluate(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 6, "moves": 3}},
            {"search": {"iterations": 300, "var": "a1", "seed": 42}},
            {"apply": {"action_var": "a1"}},
            {"search": {"iterations": 300, "var": "a2", "seed": 42}},
            {"apply": {"action_var": "a2"}},
            {"evaluate": {"iterations": 100, "var": "val"}},
            {"query": "val"},
        ])
        assert result.success
        assert isinstance(result.answer, (int, float))

    def test_inherited_compute_ops(self):
        result = self.expert.execute_trace([
            {"init": "x", "value": 5},
            {"init": "y", "value": 3},
            {"compute": {"op": "add", "args": ["x", "y"], "var": "sum"}},
            {"query": "sum"},
        ])
        assert result.success
        assert result.answer == 8

    def test_mixed_init_and_search(self):
        result = self.expert.execute_trace([
            {"init": "scale", "value": 2},
            {"init_search": {"env": "counting", "target": 6, "moves": 3}},
            {"search": {"iterations": 100, "var": "a", "seed": 1}},
            {"query": "a"},
        ])
        assert result.success
        assert result.answer in [1, 2, 3]

    def test_multiple_searches(self):
        result = self.expert.execute_trace([
            {"init_search": {"env": "counting", "target": 9, "moves": 4}},
            {"search": {"iterations": 100, "var": "a1", "seed": 1}},
            {"apply": {"action_var": "a1"}},
            {"search": {"iterations": 100, "var": "a2", "seed": 2}},
            {"apply": {"action_var": "a2"}},
            {"search": {"iterations": 100, "var": "a3", "seed": 3}},
            {"apply": {"action_var": "a3"}},
            {"query": "a3"},
        ])
        assert result.success


class TestMctsOperation:
    def test_enum_values(self):
        assert MctsOperation.INIT_SEARCH.value == "init_search"
        assert MctsOperation.SEARCH.value == "search"
        assert MctsOperation.APPLY.value == "apply"
        assert MctsOperation.EVALUATE.value == "evaluate"

    def test_enum_from_string(self):
        assert MctsOperation("search") is MctsOperation.SEARCH
