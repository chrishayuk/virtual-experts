"""Tests for MctsExpert trace execution."""

from __future__ import annotations

from chuk_virtual_expert.trace_models import ComputeOp, ComputeStep, InitStep, QueryStep

from chuk_virtual_expert_mcts import MctsExpert, MctsOperation
from chuk_virtual_expert_mcts.models import (
    ApplyStep,
    EvaluateStep,
    InitSearchStep,
    SearchStep,
)


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

    async def test_basic_init(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 5, "moves": 3}),
            ]
        )
        assert result.success
        assert result.state["_env"] == "counting"
        assert result.state["_state"]["target"] == 5
        assert result.state["_state"]["moves_left"] == 3

    async def test_default_params(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting"),
            ]
        )
        assert result.success
        assert result.state["_state"]["target"] == 10  # default

    async def test_unknown_env_fails(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="nonexistent"),
            ]
        )
        assert not result.success
        assert "Unknown environment" in result.error

    async def test_unknown_operation_via_raw_dict(self):
        result = await self.expert.execute_operation(
            "execute_trace",
            {"trace": [{"op": "bogus_op", "foo": "bar"}]},
        )
        assert not result["success"]


class TestSearch:
    def setup_method(self):
        self.expert = MctsExpert()

    async def test_produces_action(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 6, "moves": 3}),
                SearchStep(iterations=200, var="action", seed=42),
                QueryStep(var="action"),
            ]
        )
        assert result.success
        assert result.answer in [1, 2, 3]

    async def test_without_init_fails(self):
        result = await self.expert.execute_trace(
            [
                SearchStep(iterations=100),
            ]
        )
        assert not result.success
        assert "No environment" in result.error

    async def test_stores_stats(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 6, "moves": 3}),
                SearchStep(iterations=100, seed=1),
            ]
        )
        assert result.success
        stats = result.state["_search_stats"]
        assert stats["visits"] == 100
        assert "top_actions" in stats

    async def test_default_var_name(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 3, "moves": 1}),
                SearchStep(iterations=100, seed=1),
                QueryStep(var="best_action"),
            ]
        )
        assert result.success
        assert result.answer == 3

    async def test_custom_exploration(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 6, "moves": 3}),
                SearchStep(iterations=200, exploration=0.5, var="a", seed=1),
                QueryStep(var="a"),
            ]
        )
        assert result.success


class TestApply:
    def setup_method(self):
        self.expert = MctsExpert()

    async def test_direct_action(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 10, "moves": 5}),
                ApplyStep(action=3),
            ]
        )
        assert result.success
        assert result.state["_state"]["value"] == 3
        assert result.state["_state"]["moves_left"] == 4

    async def test_from_var(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 6, "moves": 3}),
                SearchStep(iterations=100, var="a", seed=42),
                ApplyStep(action_var="a"),
            ]
        )
        assert result.success
        assert result.state["_state"]["value"] > 0

    async def test_illegal_action_fails(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 10, "moves": 5}),
                ApplyStep(action=3),
                ApplyStep(action=3),
                ApplyStep(action=3),
                ApplyStep(action=3),  # value=12 > target
            ]
        )
        assert not result.success
        assert "Illegal" in result.error

    async def test_missing_var_fails(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 10, "moves": 5}),
                ApplyStep(action_var="nonexistent"),
            ]
        )
        assert not result.success
        assert "not found" in result.error

    async def test_no_action_param_fails(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 10, "moves": 5}),
                ApplyStep(),
            ]
        )
        assert not result.success
        assert "requires" in result.error


class TestEvaluate:
    def setup_method(self):
        self.expert = MctsExpert()

    async def test_non_terminal(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 3, "moves": 1}),
                EvaluateStep(iterations=200, var="v", seed=1),
                QueryStep(var="v"),
            ]
        )
        assert result.success
        assert isinstance(result.answer, (int, float))
        assert 0.0 <= float(result.answer) <= 1.0

    async def test_terminal_exact(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 3, "moves": 5}),
                ApplyStep(action=3),
                EvaluateStep(var="v"),
                QueryStep(var="v"),
            ]
        )
        assert result.success
        assert float(result.answer) == 1.0

    async def test_default_var_name(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 3, "moves": 1}),
                EvaluateStep(iterations=50, seed=1),
                QueryStep(var="value"),
            ]
        )
        assert result.success


class TestFullTraces:
    def setup_method(self):
        self.expert = MctsExpert()

    async def test_search_apply_evaluate(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 6, "moves": 3}),
                SearchStep(iterations=300, var="a1", seed=42),
                ApplyStep(action_var="a1"),
                SearchStep(iterations=300, var="a2", seed=42),
                ApplyStep(action_var="a2"),
                EvaluateStep(iterations=100, var="val"),
                QueryStep(var="val"),
            ]
        )
        assert result.success
        assert isinstance(result.answer, (int, float))

    async def test_inherited_compute_ops(self):
        result = await self.expert.execute_trace(
            [
                InitStep(var="x", value=5),
                InitStep(var="y", value=3),
                ComputeStep(compute_op=ComputeOp.ADD, args=["x", "y"], var="sum"),
                QueryStep(var="sum"),
            ]
        )
        assert result.success
        assert result.answer == 8

    async def test_mixed_init_and_search(self):
        result = await self.expert.execute_trace(
            [
                InitStep(var="scale", value=2),
                InitSearchStep(env="counting", params={"target": 6, "moves": 3}),
                SearchStep(iterations=100, var="a", seed=1),
                QueryStep(var="a"),
            ]
        )
        assert result.success
        assert result.answer in [1, 2, 3]

    async def test_multiple_searches(self):
        result = await self.expert.execute_trace(
            [
                InitSearchStep(env="counting", params={"target": 9, "moves": 4}),
                SearchStep(iterations=100, var="a1", seed=1),
                ApplyStep(action_var="a1"),
                SearchStep(iterations=100, var="a2", seed=2),
                ApplyStep(action_var="a2"),
                SearchStep(iterations=100, var="a3", seed=3),
                ApplyStep(action_var="a3"),
                QueryStep(var="a3"),
            ]
        )
        assert result.success


class TestMctsOperation:
    def test_enum_values(self):
        assert MctsOperation.INIT_SEARCH.value == "init_search"
        assert MctsOperation.SEARCH.value == "search"
        assert MctsOperation.APPLY.value == "apply"
        assert MctsOperation.EVALUATE.value == "evaluate"

    def test_enum_from_string(self):
        assert MctsOperation("search") is MctsOperation.SEARCH
