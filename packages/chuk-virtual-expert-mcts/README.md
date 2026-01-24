# chuk-virtual-expert-mcts

Pure MCTS (Monte Carlo Tree Search) virtual expert. Domain-agnostic, async-only, pydantic-native.

## Architecture

```
MctsExpert (TraceSolverExpert)
    ├── mcts.py        — Node + search algorithm
    ├── models.py      — Pydantic models (SearchResult, SearchConfig, etc.)
    ├── environment.py — Environment protocol + registry
    └── generators/    — Training data generation
```

The expert has zero domain knowledge. Environments are registered externally and provide:

```python
class Environment(Protocol):
    def get_actions(self, state) -> list: ...
    def step(self, state, action) -> state: ...
    def is_done(self, state) -> bool: ...
    def reward(self, state) -> float: ...  # 0.0-1.0
```

## Usage

```python
from chuk_virtual_expert_mcts import MctsExpert, register_environment

register_environment("my_env", MyEnvImpl())

expert = MctsExpert()
result = expert.execute_trace([
    {"init_search": {"env": "my_env"}},
    {"search": {"iterations": 1000, "var": "best"}},
    {"query": "best"},
])
```

## Trace Operations

| Operation | Description |
|-----------|-------------|
| `init_search` | Initialize environment + state |
| `search` | Run MCTS, store best action |
| `apply` | Apply action to state |
| `evaluate` | Estimate state value via rollouts |

## Async

```python
from chuk_virtual_expert_mcts import search_async, SearchConfig

result = await search_async(env, state, SearchConfig(iterations=1000))
```

## Development

```bash
make install
make test
make coverage
make demo
```
