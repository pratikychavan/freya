from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class PlannerEvent(BaseModel):
    """A single trace event emitted by the planner runner."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    event_type: Literal[
        "planner_iteration",
        "planner_validation_failed",
        "planner_terminated",
        "planner_capabilities_loaded",
        "planner_mode_selected",
        "planner_prompt_capabilities_loaded",
        "planner_observations_updated",
        "planner_context_built",
        "planner_repair_attempted",
        "planner_repair_succeeded",
        "planner_repair_failed",
        "runtime_failure_observed",
        "runtime_recovery_attempted",
        "runtime_recovery_succeeded",
        "runtime_recovery_failed",
        "runtime_failure_terminal",
        "governance_evaluated",
        "governance_policy_triggered",
        "workflow_paused_for_approval",
        "workflow_resumed_after_approval",
        "workflow_rejected_by_governance",
        "workflow_snapshot_persisted",
        "workflow_snapshot_restored",
        "workflow_state_restored",
        "workflow_lease_acquired",
        "workflow_lease_released",
        "workflow_version_conflict",
        "workflow_resume_rejected",
        "subworkflow_spawned",
        "subworkflow_completed",
        "subworkflow_failed",
        "workflow_relationship_created",
        "delegation_contract_created",
        "delegation_contract_validated",
        "delegation_contract_rejected",
        "delegation_budget_exceeded",
        "delegation_capability_missing",
        "execution_strategy_selected",
        "execution_strategy_escalated",
        "execution_strategy_blocked",
        "execution_strategy_terminated",
        "execution_cost_recorded",
        "workflow_budget_exceeded",
        "strategy_blocked_by_budget",
        "high_cost_workflow_detected",
    ]
    iteration: int
    payload: dict[str, Any] = Field(default_factory=dict)


class PlannerTrace(BaseModel):
    """Full trace for a single IterativePlannerRunner execution."""

    session_id: str
    goal: str
    events: list[PlannerEvent] = Field(default_factory=list)
    iterations_completed: int = 0
    termination_reason: str | None = None
    start_time: float = Field(default_factory=time.time)
    end_time: float | None = None
    status: Literal["SUCCESS", "FAILED", "MAX_ITERATIONS_REACHED"] = "SUCCESS"
