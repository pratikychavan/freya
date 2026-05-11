"""freya/hitl/models.py

Data models for the Advanced HITL (Human Operational Guidance) layer.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


GuidanceType = Literal[
    "cost_adjustment",
    "priority_change",
    "preference_update",
    "governance_override_request",
    "optimization_request",
    "execution_depth_change",
    "recovery_policy_change",
    "approve",
    "reject",
    "unknown",
]


class HumanGuidance(BaseModel):
    """Parsed and structured form of a user's operational guidance input."""

    guidance_id: str
    raw_input: str
    interpreted_intent: str              # one-line, human-readable interpretation
    guidance_type: GuidanceType
    extracted_constraints: dict[str, Any] = Field(default_factory=dict)
    extracted_preferences: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.8
    requires_governance_review: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parse_method: Literal["llm", "deterministic"] = "deterministic"


class GuidanceApplicationResult(BaseModel):
    """Outcome of applying a HumanGuidance to the workflow state."""

    success: bool
    applied_changes: list[str] = Field(default_factory=list)
    workflow_updates: list[str] = Field(default_factory=list)
    governance_actions: list[str] = Field(default_factory=list)
    narrative_summary: str


class GuidanceGovernanceDecision(BaseModel):
    """Governance verdict for a piece of human guidance."""

    allowed: bool
    reason: str
    requires_approval: bool = False
    risk_level: Literal["none", "low", "medium", "high"] = "none"


class GuidanceHistoryEntry(BaseModel):
    """An immutable audit record of one Human Guidance event."""

    guidance_id: str
    raw_input: str
    interpreted_intent: str
    guidance_type: GuidanceType
    result_summary: str
    governance_decision: str   # "allowed" | "blocked" | "escalated"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GuidanceAuditTrail(BaseModel):
    """Full ordered history of guidance events for a workflow session."""

    session_id: str
    entries: list[GuidanceHistoryEntry] = Field(default_factory=list)

    def add(self, guidance: HumanGuidance, result: GuidanceApplicationResult, gov: str) -> None:
        self.entries.append(
            GuidanceHistoryEntry(
                guidance_id=guidance.guidance_id,
                raw_input=guidance.raw_input,
                interpreted_intent=guidance.interpreted_intent,
                guidance_type=guidance.guidance_type,
                result_summary=result.narrative_summary,
                governance_decision=gov,
            )
        )

    def render(self) -> str:
        if not self.entries:
            return "  No guidance recorded."
        lines = []
        for i, e in enumerate(self.entries, 1):
            ts = e.timestamp.strftime("%H:%M:%S")
            lines.append(f"  {i}. [{ts}] {e.guidance_type}  —  {e.interpreted_intent}")
            lines.append(f"     Result: {e.result_summary}  |  Governance: {e.governance_decision}")
        return "\n".join(lines)
