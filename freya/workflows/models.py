from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class RelationshipType:
    """String constants for workflow relationship types."""

    SPAWNED_SUBWORKFLOW = "spawned_subworkflow"
    DELEGATED_EXECUTION = "delegated_execution"
    RECOVERY_SUBWORKFLOW = "recovery_subworkflow"


class WorkflowRelationship(BaseModel):
    """Records a directed parent → child workflow relationship."""

    relationship_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_session_id: str
    child_session_id: str
    relationship_type: str = RelationshipType.SPAWNED_SUBWORKFLOW
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
