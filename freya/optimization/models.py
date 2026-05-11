"""freya/optimization/models.py

Data models for the Proactive Operational Optimization layer.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OptimizationOpportunity(BaseModel):
    """A single identified optimization opportunity."""

    opportunity_id: str
    title: str
    description: str
    optimization_type: Literal[
        "cost", "speed", "quality", "governance", "cognitive", "delegation"
    ]
    estimated_cost_delta: float | None = None      # negative = savings
    estimated_time_delta: float | None = None      # in hours, negative = faster
    estimated_quality_delta: float | None = None   # -1..+1, negative = downgrade
    confidence_score: float = 0.8                  # 0-1
    governance_impact: str | None = None           # e.g. "no_change", "requires_approval"
    constraint_updates: dict[str, Any] = Field(default_factory=dict)
    # Applied to WorkflowSteeringState when user approves


class OptimizationProposal(BaseModel):
    """A package of one or more OptimizationOpportunities with a recommendation."""

    proposal_id: str
    reason: str                              # why this proposal is surfaced
    opportunities: list[OptimizationOpportunity]
    recommended_action: str                  # e.g. "Apply cost optimization"
    requires_approval: bool = False
    evaluation: "OptimizationEvaluation | None" = None


class OptimizationEvaluation(BaseModel):
    """Scored summary of a set of OptimizationOpportunities."""

    total_savings: float                     # INR, negative means cost-saving
    execution_impact: str                    # human-readable description
    governance_risk: Literal["none", "low", "medium", "high"] = "none"
    confidence_score: float = 0.8
    net_value_score: float = 0.0             # composite benefit score (-1..1)

    def confidence_label(self) -> str:
        if self.confidence_score >= 0.85:
            return "Strongly recommended"
        if self.confidence_score >= 0.65:
            return "Recommended"
        if self.confidence_score >= 0.45:
            return "Possible optimization available"
        return "Speculative — review carefully"


# Rebuild forward refs
OptimizationProposal.model_rebuild()
