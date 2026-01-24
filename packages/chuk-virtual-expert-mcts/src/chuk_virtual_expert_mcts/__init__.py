"""chuk-virtual-expert-mcts: Pure MCTS search expert.

Domain-agnostic Monte Carlo Tree Search as a TraceSolverExpert.
Register environments externally, then search via trace operations.

Usage:
    from chuk_virtual_expert_mcts import MctsExpert, register_environment, Environment

    class MyEnv:
        def get_actions(self, state): ...
        def step(self, state, action): ...
        def is_done(self, state): ...
        def reward(self, state): ...
        def initial(self, **kwargs): ...

    register_environment("my_env", MyEnv())

    expert = MctsExpert()
    result = expert.execute_trace([
        {"init_search": {"env": "my_env"}},
        {"search": {"iterations": 1000, "var": "best"}},
        {"query": "best"},
    ])
"""

from chuk_virtual_expert_mcts.environment import (
    Environment,
    get_environment,
    register_environment,
    registered_environments,
)
from chuk_virtual_expert_mcts.expert import MctsExpert
from chuk_virtual_expert_mcts.generators import MctsTraceGenerator
from chuk_virtual_expert_mcts.mcts import Node, search, search_async
from chuk_virtual_expert_mcts.models import (
    ActionStat,
    MctsOperation,
    SearchConfig,
    SearchResult,
)

__all__ = [
    "MctsExpert",
    "Environment",
    "register_environment",
    "get_environment",
    "registered_environments",
    "MctsTraceGenerator",
    "Node",
    "search",
    "search_async",
    "ActionStat",
    "MctsOperation",
    "SearchConfig",
    "SearchResult",
]

__version__ = "1.0.0"
