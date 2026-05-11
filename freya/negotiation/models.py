"""freya/negotiation/models.py

Data models for the Distributed Operational Negotiation layer.

Design rules:
  - All negotiation is explicit, bounded, and reversible
  - No autonomous agent behaviour — all decisions are explainable
  - Governance guarantees are never negotiated away
  - Contracts expire; degradation recovers
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PriorityLevel      = Literal["critical", "high", "standard", "low", "background"]
FlexibilityLevel   = Literal["rigid", "low", "moderate", "high", "elastic"]
DegradationMode    = Literal[
    "none",
    "reduced_reasoning",
    "lightweight_planning",
    "skip_optimization",
    "compressed_analysis",
    "deferred_retries",
    "governance_batching",
]
GovernanceRisk     = Literal["none", "low", "medium", "high", "critical"]
ContractStatus     = Literal["active", "expired", "reverted", "pending"]
NegotiationStrategy = Literal[
    "temporary_degradation",
    "reasoning_compression",
    "optimization_deferral",
    "staged_execution",
    "elastic_reallocation",
    "governance_batching",
    "no_action",
]


class OperationalNegotiationRequest(BaseModel):
    """A workflow's request for additional operational capacity."""
    workflow_id: str
    requested_resource: str          # "reasoning_budget"|"approval_bandwidth"|"optimization_budget"
    requested_capacity: float        # normalized share, 0.0–1.0
    operational_reason: str
    priority_level: PriorityLevel = "standard"
    flexibility_level: FlexibilityLevel = "moderate"


class NegotiationProposal(BaseModel):
    """A coordination proposal spanning multiple workflows."""
    proposal_id: str
    participating_workflows: list[str]
    proposed_adjustments: list[str]  # human-readable descriptions
    expected_operational_impact: str
    governance_risk: GovernanceRisk = "none"
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.80)
    strategy_used: NegotiationStrategy = "no_action"


class WorkflowDegradationPlan(BaseModel):
    """A bounded, reversible quality reduction for a workflow."""
    workflow_id: str
    degradation_mode: DegradationMode = "none"
    reduced_capabilities: list[str] = Field(default_factory=list)
    expected_quality_impact: str = "minimal"
    reversibility: bool = True
    recovery_trigger: str = "resource_pressure_below_threshold"
    minimum_quality_floor: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="No degradation may reduce workflow quality below this floor.",
    )


class ElasticResourceAdjustment(BaseModel):
    """A temporary capacity transfer between two workflows."""
    resource_id: str
    source_workflow: str
    target_workflow: str
    adjustment_amount: float = Field(ge=0.0, le=1.0)
    temporary: bool = True
    duration_hint: str = "until_pressure_normalizes"


class NegotiationContract(BaseModel):
    """Persisted negotiation agreement — bounded, auditable, reversible."""
    contract_id: str
    workflow_id: str
    contract_type: str               # "degradation"|"resource_borrow"|"deferral"|"batching"
    terms: dict = Field(default_factory=dict)
    status: ContractStatus = "active"
    reversible: bool = True
    expiry_trigger: str = "pressure_normalized"
    audit_log: list[str] = Field(default_factory=list)
