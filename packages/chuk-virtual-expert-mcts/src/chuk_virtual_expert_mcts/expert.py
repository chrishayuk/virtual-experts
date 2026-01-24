"""MctsExpert — pure MCTS search via TraceSolverExpert.

Domain-agnostic, async-native, pydantic-native.
Environments are registered externally via register_environment().
"""

from __future__ import annotations

from typing import Any, ClassVar

from chuk_virtual_expert.trace_models import BaseTraceStep, TraceStep
from chuk_virtual_expert.trace_solver import TraceSolverExpert
from pydantic import TypeAdapter

from chuk_virtual_expert_mcts.environment import (
    Environment,
    get_environment,
    registered_environments,
)
from chuk_virtual_expert_mcts.mcts import search
from chuk_virtual_expert_mcts.models import (
    MCTS_STEP_TYPES,
    ApplyStep,
    EvaluateStep,
    InitSearchStep,
    SearchConfig,
    SearchStep,
)

# Base step adapter for parsing standard trace steps
_base_step_adapter: TypeAdapter[TraceStep] = TypeAdapter(TraceStep)


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
        "mcts",
        "monte carlo",
        "tree search",
        "best action",
        "search tree",
    ]

    def can_handle(self, prompt: str) -> bool:
        keywords = list(self._KEYWORDS) + registered_environments()
        p = prompt.lower()
        return any(kw in p for kw in keywords)

    async def execute_operation(
        self,
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Parse trace steps (MCTS + base) and execute."""
        if operation != "execute_trace" or params is None:
            return {
                "success": False,
                "answer": None,
                "state": {},
                "error": f"Unknown operation: {operation}",
                "steps_executed": 0,
                "formatted": "",
            }

        raw_steps = params.get("trace", [])
        if not isinstance(raw_steps, list):
            return {
                "success": False,
                "answer": None,
                "state": {},
                "error": "Trace must be a list",
                "steps_executed": 0,
                "formatted": "",
            }

        try:
            steps = [self._parse_step(s) for s in raw_steps]
        except Exception as e:
            return {
                "success": False,
                "answer": None,
                "state": {},
                "error": str(e),
                "steps_executed": 0,
                "formatted": "",
            }

        result = await self.execute_trace(steps)
        return {
            "success": result.success,
            "answer": result.answer,
            "state": result.state,
            "error": result.error,
            "steps_executed": result.steps_executed,
            "formatted": str(result.answer) if result.answer is not None else "",
        }

    def _parse_step(self, raw: dict[str, Any] | BaseTraceStep) -> BaseTraceStep:
        """Parse a raw dict into a typed step (MCTS or base)."""
        if isinstance(raw, BaseTraceStep):
            return raw

        op = raw.get("op")
        if op and op in MCTS_STEP_TYPES:
            return MCTS_STEP_TYPES[op].model_validate(raw)

        # Fall back to base step adapter
        return _base_step_adapter.validate_python(raw)

    async def execute_step(self, step: BaseTraceStep, state: dict[str, Any]) -> dict[str, Any]:
        """Execute MCTS-specific trace steps."""
        if isinstance(step, InitSearchStep):
            return self._init_search(step, state)
        elif isinstance(step, SearchStep):
            return self._do_search(step, state)
        elif isinstance(step, ApplyStep):
            return self._apply(step, state)
        elif isinstance(step, EvaluateStep):
            return self._evaluate(step, state)
        else:
            raise ValueError(f"Unknown MCTS step type: {type(step).__name__}")

    def _get_env(self, state: dict[str, Any]) -> Environment:
        env_name = state.get("_env")
        if not env_name:
            raise ValueError("No environment initialized. Use init_search first.")
        return get_environment(env_name)

    def _init_search(self, step: InitSearchStep, state: dict[str, Any]) -> dict[str, Any]:
        env = get_environment(step.env)

        if hasattr(env, "initial"):
            env_state = env.initial(**step.params)
        else:
            raise ValueError(f"Environment {step.env!r} has no initial() method")

        state["_env"] = step.env
        state["_state"] = env_state
        return state

    def _do_search(self, step: SearchStep, state: dict[str, Any]) -> dict[str, Any]:
        env = self._get_env(state)

        config = SearchConfig(
            iterations=step.iterations,
            exploration=step.exploration,
            seed=step.seed,
        )

        result = search(env=env, state=state["_state"], config=config)

        state[step.var] = result.best_action
        state["_search_stats"] = result.model_dump(exclude={"action_stats"})
        state["_search_stats"]["top_actions"] = [a.model_dump() for a in result.action_stats[:5]]
        return state

    def _apply(self, step: ApplyStep, state: dict[str, Any]) -> dict[str, Any]:
        env = self._get_env(state)
        env_state = state["_state"]

        # Skip apply if environment is already terminal
        if env.is_done(env_state):
            return state

        if step.action_var is not None:
            if step.action_var not in state:
                raise ValueError(f"Variable {step.action_var!r} not found")
            action = state[step.action_var]
            if action is None:
                raise ValueError(
                    f"No action available in {step.action_var!r} (environment may be terminal)"
                )
        elif step.action is not None:
            action = step.action
        else:
            raise ValueError("apply requires 'action' or 'action_var'")

        legal = env.get_actions(env_state)
        if action not in legal:
            raise ValueError(f"Illegal action: {action!r}. Legal: {legal}")

        state["_state"] = env.step(env_state, action)
        return state

    def _evaluate(self, step: EvaluateStep, state: dict[str, Any]) -> dict[str, Any]:
        env = self._get_env(state)
        env_state = state["_state"]

        if env.is_done(env_state):
            state[step.var] = env.reward(env_state)
            return state

        config = SearchConfig(
            iterations=step.iterations,
            seed=step.seed,
        )

        result = search(env=env, state=env_state, config=config)
        state[step.var] = result.value
        return state
