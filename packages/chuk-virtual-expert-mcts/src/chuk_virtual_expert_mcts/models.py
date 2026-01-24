"""Pydantic models for MCTS search."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MctsOperation(str, Enum):
    """Trace operations supported by MctsExpert."""

    INIT_SEARCH = "init_search"
    SEARCH = "search"
    APPLY = "apply"
    EVALUATE = "evaluate"


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
