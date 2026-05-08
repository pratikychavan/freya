from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from freya.governance.state import WorkflowState


class ApprovalRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    iteration: int
    proposed_dag: dict
    governance_reason: str
    risk_level: str | None = None
    triggered_policies: list[str] = Field(default_factory=list)
    observation_summaries: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state: WorkflowState = WorkflowState.PAUSED_FOR_APPROVAL

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovalRequest":
        """Reconstruct from a previously serialized dict."""
        return cls.model_validate(data)
