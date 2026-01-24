"""chuk-virtual-expert-mcts: Pure MCTS search expert.

Domain-agnostic Monte Carlo Tree Search as a TraceSolverExpert.
Register environments externally, then search via trace operations.

Usage:
    import asyncio
    from chuk_virtual_expert.trace_models import QueryStep
    from chuk_virtual_expert_mcts import MctsExpert, register_environment
    from chuk_virtual_expert_mcts.models import InitSearchStep, SearchStep

    register_environment("my_env", MyEnv())

    async def main():
        expert = MctsExpert()
        result = await expert.execute_trace([
            InitSearchStep(env="my_env", params={"target": 10}),
            SearchStep(iterations=1000, var="best"),
            QueryStep(var="best"),
        ])

    asyncio.run(main())
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
    ApplyStep,
    EvaluateStep,
    InitSearchStep,
    MctsOperation,
    SearchConfig,
    SearchResult,
    SearchStep,
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
    "ApplyStep",
    "EvaluateStep",
    "InitSearchStep",
    "MctsOperation",
    "SearchConfig",
    "SearchResult",
    "SearchStep",
]

__version__ = "1.0.0"
