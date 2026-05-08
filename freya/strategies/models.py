from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ExecutionStrategy(str, Enum):
    """Canonical execution strategies available to the adaptive runner."""

    DETERMINISTIC = "deterministic"
    COGNITIVE = "cognitive"
    REPAIR = "repair"
    RECOVERY = "recovery"
    DELEGATION = "delegation"
    HUMAN_APPROVAL = "human_approval"
    TERMINATE = "terminate"


class StrategyDecision(BaseModel):
    """Explicit reasoning record for a single strategy selection."""

    strategy: ExecutionStrategy
    reason: str
    confidence: float | None = None
    triggered_by: list[str] = Field(default_factory=list)
    governance_constraints: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
