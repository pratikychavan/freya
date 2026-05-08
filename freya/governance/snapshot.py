from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from freya.governance.state import WorkflowState


class WorkflowSnapshot(BaseModel):
    """Durable snapshot of workflow execution state for crash-safe resume."""

    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    workflow_state: WorkflowState
    iteration: int
    planning_mode: str
    goal: str
    completed_tasks: list[str] = Field(default_factory=list)
    failed_tasks: list[str] = Field(default_factory=list)
    task_results: dict = Field(default_factory=dict)
    recent_observations: list[dict] = Field(default_factory=list)
    memory_state: dict = Field(default_factory=dict)
    paused_dag_fragment: dict | None = None
    approval_request_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Versioning + concurrency
    version: int = 0
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    # Delegation contract lineage — serialized DelegationContract dicts
    active_contracts: list[dict] = Field(default_factory=list)
    # Adaptive execution strategy
    current_strategy: str | None = None
    strategy_history: list[dict] = Field(default_factory=list)
