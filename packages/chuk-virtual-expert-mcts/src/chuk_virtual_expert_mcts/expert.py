"""MctsExpert — pure MCTS search via TraceSolverExpert.

Domain-agnostic, async-native, pydantic-native.
Environments are registered externally via register_environment().
"""

from __future__ import annotations

from typing import Any, ClassVar

from chuk_virtual_expert.trace_solver import TraceSolverExpert

from chuk_virtual_expert_mcts.environment import Environment, get_environment, registered_environments
from chuk_virtual_expert_mcts.mcts import search
from chuk_virtual_expert_mcts.models import MctsOperation, SearchConfig


class MctsExpert(TraceSolverExpert):
    """Pure MCTS search expert.

    Trace operations:
        init_search: Set up environment and initial state
        search: Run MCTS iterations, store best action
        apply: Apply an action to current state
        evaluate: Estimate value of current state via rollouts
    """

    name: ClassVar[str] = "mcts"
    description: ClassVar[str] = "Searches decision trees using Monte Carlo Tree Search"
    version: ClassVar[str] = "1.0.0"
    priority: ClassVar[int] = 10

    cot_examples_file: ClassVar[str] = "../data/cot_examples.json"
    calibration_file: ClassVar[str] = "../data/calibration.json"

    _KEYWORDS: ClassVar[list[str]] = [
        "mcts", "monte carlo", "tree search", "best action", "search tree",
    ]

    def can_handle(self, prompt: str) -> bool:
        keywords = list(self._KEYWORDS) + registered_environments()
        p = prompt.lower()
        return any(kw in p for kw in keywords)

    def execute_step(self, step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        op = MctsOperation(next(iter(step)))

        if op is MctsOperation.INIT_SEARCH:
            return self._init_search(step[op.value], state)
        elif op is MctsOperation.SEARCH:
            return self._do_search(step[op.value], state)
        elif op is MctsOperation.APPLY:
            return self._apply(step[op.value], state)
        elif op is MctsOperation.EVALUATE:
            return self._evaluate(step[op.value], state)

    def _get_env(self, state: dict[str, Any]) -> Environment:
        env_name = state.get("_env")
        if not env_name:
            raise ValueError("No environment initialized. Use init_search first.")
        return get_environment(env_name)

    def _init_search(self, params: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        env_name = str(params.get("env", ""))
        env = get_environment(env_name)

        init_kwargs = {k: v for k, v in params.items() if k != "env"}

        if hasattr(env, "initial"):
            env_state = env.initial(**init_kwargs)
        else:
            raise ValueError(f"Environment {env_name!r} has no initial() method")

        state["_env"] = env_name
        state["_state"] = env_state
        return state

    def _do_search(self, params: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        env = self._get_env(state)

        config = SearchConfig(
            iterations=int(params.get("iterations", 1000)),
            exploration=float(params.get("exploration", 1.41)),
            seed=params.get("seed"),
        )
        var = str(params.get("var", "best_action"))

        result = search(env=env, state=state["_state"], config=config)

        state[var] = result.best_action
        state["_search_stats"] = result.model_dump(exclude={"action_stats"})
        state["_search_stats"]["top_actions"] = [
            a.model_dump() for a in result.action_stats[:5]
        ]
        return state

    def _apply(self, params: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        env = self._get_env(state)
        env_state = state["_state"]

        # Skip apply if environment is already terminal
        if env.is_done(env_state):
            return state

        if "action_var" in params:
            var_name = str(params["action_var"])
            if var_name not in state:
                raise ValueError(f"Variable {var_name!r} not found")
            action = state[var_name]
            if action is None:
                raise ValueError(f"No action available in {var_name!r} (environment may be terminal)")
        elif "action" in params:
            action = params["action"]
        else:
            raise ValueError("apply requires 'action' or 'action_var'")

        legal = env.get_actions(env_state)
        if action not in legal:
            raise ValueError(f"Illegal action: {action!r}. Legal: {legal}")

        state["_state"] = env.step(env_state, action)
        return state

    def _evaluate(self, params: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        env = self._get_env(state)
        env_state = state["_state"]
        var = str(params.get("var", "value"))

        if env.is_done(env_state):
            state[var] = env.reward(env_state)
            return state

        config = SearchConfig(
            iterations=int(params.get("iterations", 500)),
            seed=params.get("seed"),
        )

        result = search(env=env, state=env_state, config=config)
        state[var] = result.value
        return state
