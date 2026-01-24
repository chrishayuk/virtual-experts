"""Generator for MCTS training traces."""

from __future__ import annotations

import random
from typing import Any

from chuk_virtual_expert_mcts.models import MctsOperation


class MctsTraceGenerator:
    """Generates MCTS trace examples for training.

    Produces traces that exercise init_search, search, apply, evaluate
    operations across registered environments.
    """

    def generate_search(self, env_name: str, **init_kwargs: Any) -> dict[str, Any]:
        """Generate a search trace."""
        iterations = random.choice([100, 200, 500, 1000])
        return {
            "expert": "mcts",
            "trace": [
                {MctsOperation.INIT_SEARCH.value: {"env": env_name, **init_kwargs}},
                {MctsOperation.SEARCH.value: {"iterations": iterations, "var": "best_action"}},
                {"query": "best_action"},
            ],
        }

    def generate_search_and_apply(self, env_name: str, **init_kwargs: Any) -> dict[str, Any]:
        """Generate a search-then-apply trace."""
        iterations = random.choice([200, 500, 1000])
        return {
            "expert": "mcts",
            "trace": [
                {MctsOperation.INIT_SEARCH.value: {"env": env_name, **init_kwargs}},
                {MctsOperation.SEARCH.value: {"iterations": iterations, "var": "a1"}},
                {MctsOperation.APPLY.value: {"action_var": "a1"}},
                {MctsOperation.SEARCH.value: {"iterations": iterations, "var": "a2"}},
                {"query": "a2"},
            ],
        }

    def generate_evaluate(self, env_name: str, **init_kwargs: Any) -> dict[str, Any]:
        """Generate an evaluate trace."""
        iterations = random.choice([200, 500, 1000])
        return {
            "expert": "mcts",
            "trace": [
                {MctsOperation.INIT_SEARCH.value: {"env": env_name, **init_kwargs}},
                {MctsOperation.EVALUATE.value: {"iterations": iterations, "var": "value"}},
                {"query": "value"},
            ],
        }

    def generate_multi_step(self, env_name: str, n_steps: int = 3, **init_kwargs: Any) -> dict[str, Any]:
        """Generate a multi-step search-apply trace."""
        iterations = random.choice([100, 200, 500])
        trace: list[dict] = [
            {MctsOperation.INIT_SEARCH.value: {"env": env_name, **init_kwargs}},
        ]
        for i in range(n_steps):
            var = f"a{i + 1}"
            trace.append({MctsOperation.SEARCH.value: {"iterations": iterations, "var": var}})
            trace.append({MctsOperation.APPLY.value: {"action_var": var}})

        trace.append({MctsOperation.EVALUATE.value: {"var": "final_value"}})
        trace.append({"query": "final_value"})
        return {
            "expert": "mcts",
            "trace": trace,
        }

    def generate(self, env_name: str, n: int = 20, **init_kwargs: Any) -> list[dict[str, Any]]:
        """Generate n mixed MCTS traces."""
        generators = [
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
