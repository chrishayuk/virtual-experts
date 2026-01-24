"""Generator for MCTS training traces."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

from chuk_virtual_expert.trace_example import TraceExample
from chuk_virtual_expert.trace_models import QueryStep

from chuk_virtual_expert_mcts.models import (
    ApplyStep,
    EvaluateStep,
    InitSearchStep,
    SearchStep,
)


class MctsTraceGenerator:
    """Generates MCTS trace examples for training.

    Produces traces that exercise init_search, search, apply, evaluate
    operations across registered environments.
    """

    def generate_search(self, env_name: str, **init_kwargs: Any) -> TraceExample:
        """Generate a search trace."""
        iterations = random.choice([100, 200, 500, 1000])
        return TraceExample(
            expert="mcts",
            query=f"Search {env_name} for best action ({iterations} iterations)",
            trace=[
                InitSearchStep(env=env_name, params=init_kwargs),
                SearchStep(iterations=iterations, var="best_action"),
                QueryStep(var="best_action"),
            ],
            expected_operation="execute_trace",
        )

    def generate_search_and_apply(self, env_name: str, **init_kwargs: Any) -> TraceExample:
        """Generate a search-then-apply trace."""
        iterations = random.choice([200, 500, 1000])
        return TraceExample(
            expert="mcts",
            query=f"Search {env_name}, apply, then search again ({iterations} iterations)",
            trace=[
                InitSearchStep(env=env_name, params=init_kwargs),
                SearchStep(iterations=iterations, var="a1"),
                ApplyStep(action_var="a1"),
                SearchStep(iterations=iterations, var="a2"),
                QueryStep(var="a2"),
            ],
            expected_operation="execute_trace",
        )

    def generate_evaluate(self, env_name: str, **init_kwargs: Any) -> TraceExample:
        """Generate an evaluate trace."""
        iterations = random.choice([200, 500, 1000])
        return TraceExample(
            expert="mcts",
            query=f"Evaluate {env_name} position ({iterations} iterations)",
            trace=[
                InitSearchStep(env=env_name, params=init_kwargs),
                EvaluateStep(iterations=iterations, var="value"),
                QueryStep(var="value"),
            ],
            expected_operation="execute_trace",
        )

    def generate_multi_step(
        self, env_name: str, n_steps: int = 3, **init_kwargs: Any
    ) -> TraceExample:
        """Generate a multi-step search-apply trace."""
        iterations = random.choice([100, 200, 500])
        trace: list = [
            InitSearchStep(env=env_name, params=init_kwargs),
        ]
        for i in range(n_steps):
            var = f"a{i + 1}"
            trace.append(SearchStep(iterations=iterations, var=var))
            trace.append(ApplyStep(action_var=var))

        trace.append(EvaluateStep(var="final_value"))
        trace.append(QueryStep(var="final_value"))
        return TraceExample(
            expert="mcts",
            query=f"Multi-step {env_name} search ({n_steps} steps, {iterations} iterations)",
            trace=trace,
            expected_operation="execute_trace",
        )

    def generate(self, env_name: str, n: int = 20, **init_kwargs: Any) -> list[TraceExample]:
        """Generate n mixed MCTS traces."""
        generators: list[Callable[..., TraceExample]] = [
            self.generate_search,
            self.generate_search_and_apply,
            self.generate_evaluate,
            self.generate_multi_step,
        ]
        examples = []
        for _ in range(n):
            gen = random.choice(generators)
            examples.append(gen(env_name, **init_kwargs))
        return examples
