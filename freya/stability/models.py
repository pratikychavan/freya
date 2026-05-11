"""freya/stability/models.py

Data models for the Operational Stabilization + Adaptive Trust layer.

Design rules:
  - No social scoring semantics
  - All state is workflow-scoped, not user-scoped
  - Trust is recoverable (no permanent distrust states)
  - Stability scores drive guidance, never hard locks
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DriftLevel        = Literal["none", "mild", "moderate", "severe"]
TrustLevel        = Literal["established", "standard", "cautious", "restricted"]
TrustTrend        = Literal["improving", "stable", "declining"]
GovernanceScrutiny = Literal["minimal", "standard", "elevated", "high", "maximum"]
OperationalMode   = Literal[
    "cost_optimization",
    "balanced",
    "quality_optimization",
    "speed_optimization",
    "governance_safe",
    "unknown",
]


class OperationalStabilityState(BaseModel):
    """Current stability snapshot for a workflow."""
    workflow_id: str
    stability_score: float = Field(ge=0.0, le=1.0, description="1.0 = fully stable")
    drift_level: DriftLevel = "none"
    reversal_count: int = 0
    active_operational_mode: OperationalMode = "balanced"
    stabilization_recommended: bool = False


class AdaptiveTrustState(BaseModel):
    """Workflow-scoped operational trust — NOT a human morality score."""
    workflow_id: str
    trust_level: TrustLevel = "standard"
    governance_scrutiny: GovernanceScrutiny = "standard"
    recent_governance_events: list[str] = Field(default_factory=list)
    trust_trend: TrustTrend = "stable"
    compliant_action_streak: int = 0   # consecutive compliant actions since last conflict
    total_bypass_attempts: int = 0


class OperationalWeightProfile(BaseModel):
    """Hierarchical weighting of operational constraints and preferences."""
    hard_constraints: dict = Field(
        default_factory=dict,
        description="Non-negotiable: budget ceiling, governance rules, etc.",
    )
    soft_constraints: dict = Field(
        default_factory=dict,
        description="Preferred but tradeable: metro proximity, hotel tier, etc.",
    )
    weighted_preferences: dict = Field(
        default_factory=dict,
        description="Numeric weights 0.0–1.0 per operational dimension.",
    )
    operational_priorities: list[str] = Field(
        default_factory=list,
        description="Ordered priorities, highest first.",
    )


class StabilizationRecommendation(BaseModel):
    """A collaborative suggestion to move the workflow toward a stable mode."""
    title: str
    reason: str
    recommended_mode: OperationalMode
    expected_impact: str
    options: list[str] = Field(default_factory=list)
