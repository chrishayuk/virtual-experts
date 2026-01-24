"""Pydantic models for MCTS search."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from chuk_virtual_expert.trace_models import BaseTraceStep
from pydantic import BaseModel, Field


class MctsOperation(str, Enum):
    """Trace operations supported by MctsExpert."""

    INIT_SEARCH = "init_search"
    SEARCH = "search"
    APPLY = "apply"
    EVALUATE = "evaluate"


# --- MCTS-specific typed trace steps ---


class InitSearchStep(BaseTraceStep):
    """Initialize MCTS search environment and state."""

    op: Literal["init_search"] = "init_search"
    env: str
    params: dict[str, Any] = Field(default_factory=dict)


class SearchStep(BaseTraceStep):
    """Run MCTS search iterations."""

    op: Literal["search"] = "search"
    iterations: int = 1000
    exploration: float = 1.41
    seed: int | None = None
    var: str = "best_action"


class ApplyStep(BaseTraceStep):
    """Apply an action to current state."""

    op: Literal["apply"] = "apply"
    action_var: str | None = None
    action: Any | None = None


class EvaluateStep(BaseTraceStep):
    """Evaluate current state via rollouts."""

    op: Literal["evaluate"] = "evaluate"
    iterations: int = 500
    seed: int | None = None
    var: str = "value"


# Map of MCTS op names to step types (for parsing raw dicts)
MCTS_STEP_TYPES: dict[str, type[BaseTraceStep]] = {
    "init_search": InitSearchStep,
    "search": SearchStep,
    "apply": ApplyStep,
    "evaluate": EvaluateStep,
}


class ActionStat(BaseModel):
    """Statistics for a single action from search."""

    action: Any
    visits: int = 0
    value: float = 0.0


class SearchResult(BaseModel):
    """Result from an MCTS search."""

    best_action: Any | None = None
    visits: int = 0
    value: float = 0.0
    action_stats: list[ActionStat] = Field(default_factory=list)


class SearchConfig(BaseModel):
    """Configuration for an MCTS search."""

    iterations: int = 1000
    exploration: float = 1.41
    seed: int | None = None
