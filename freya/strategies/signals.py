from __future__ import annotations

from pydantic import BaseModel, Field


class RuntimeSignals(BaseModel):
    """Snapshot of observable runtime signals used by the strategy engine.

    Signals are collected by the runner at each iteration boundary and passed
    to :class:`~freya.strategies.engine.ExecutionStrategyEngine` to inform
    the next strategy choice.
    """

    validation_failures: int = 0
    runtime_failures: int = 0
    governance_blocks: int = 0
    delegation_failures: int = 0
    recovery_attempts: int = 0
    planner_iterations: int = 0
    confidence_score: float | None = None
    pending_approvals: int = 0
