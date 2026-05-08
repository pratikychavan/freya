from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class InterventionDecision(str, Enum):
    APPROVE = "approve"
    REQUIRE_APPROVAL = "require_approval"
    REJECT = "reject"


class GovernanceDecision(BaseModel):
    decision: InterventionDecision
    reason: str
    risk_level: str | None = None
    triggered_policies: list[str] = Field(default_factory=list)
