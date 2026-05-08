from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Canonical runtime event type constants
# ---------------------------------------------------------------------------

class EventType:
    """String constants for all canonical RuntimeEvent types."""

    PLANNER_ITERATION_STARTED = "planner_iteration_started"
    PLANNER_ITERATION_COMPLETED = "planner_iteration_completed"
    PLANNER_TERMINATED = "planner_terminated"
    PLANNER_CAPABILITIES_LOADED = "planner_capabilities_loaded"
    PLANNER_MODE_SELECTED = "planner_mode_selected"
    PLANNER_VALIDATION_FAILED = "planner_validation_failed"
    PLANNER_REPAIR_ATTEMPTED = "planner_repair_attempted"
    PLANNER_REPAIR_SUCCEEDED = "planner_repair_succeeded"
    PLANNER_REPAIR_FAILED = "planner_repair_failed"
    PLANNER_OBSERVATIONS_UPDATED = "planner_observations_updated"

    RUNTIME_FAILURE_OBSERVED = "runtime_failure_observed"
    RUNTIME_RECOVERY_ATTEMPTED = "runtime_recovery_attempted"
    RUNTIME_RECOVERY_SUCCEEDED = "runtime_recovery_succeeded"
    RUNTIME_RECOVERY_FAILED = "runtime_recovery_failed"
    RUNTIME_FAILURE_TERMINAL = "runtime_failure_terminal"

    GOVERNANCE_EVALUATED = "governance_evaluated"
    GOVERNANCE_POLICY_TRIGGERED = "governance_policy_triggered"

    WORKFLOW_PAUSED_FOR_APPROVAL = "workflow_paused_for_approval"
    WORKFLOW_RESUMED_AFTER_APPROVAL = "workflow_resumed_after_approval"
    WORKFLOW_REJECTED_BY_GOVERNANCE = "workflow_rejected_by_governance"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_SNAPSHOT_PERSISTED = "workflow_snapshot_persisted"
    WORKFLOW_SNAPSHOT_RESTORED = "workflow_snapshot_restored"
    WORKFLOW_STATE_RESTORED = "workflow_state_restored"
    WORKFLOW_LEASE_ACQUIRED = "workflow_lease_acquired"
    WORKFLOW_LEASE_RELEASED = "workflow_lease_released"
    WORKFLOW_VERSION_CONFLICT = "workflow_version_conflict"
    WORKFLOW_RESUME_REJECTED = "workflow_resume_rejected"

    SUBWORKFLOW_SPAWNED = "subworkflow_spawned"
    SUBWORKFLOW_COMPLETED = "subworkflow_completed"
    SUBWORKFLOW_FAILED = "subworkflow_failed"
    WORKFLOW_RELATIONSHIP_CREATED = "workflow_relationship_created"

    SUBSCRIBER_FAILURE = "subscriber_failure"


class RuntimeEvent(BaseModel):
    """A single runtime event emitted by the Freya event bus."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    session_id: str
    workflow_state: str | None = None
    iteration: int | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)
