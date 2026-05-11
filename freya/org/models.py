"""freya/org/models.py

Data models for the Organizational Policy + Multi-Workflow Cognition layer.

Design rules:
  - All prioritization is policy-driven and explainable
  - No opaque centralized control
  - Coordination is transparent and auditable
  - No social scoring; all state is workflow/domain scoped
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

OperationalCriticality = Literal["critical", "high", "standard", "low", "background"]
GovernanceLevel        = Literal["strict", "standard", "flexible", "minimal"]
ContentionLevel        = Literal["none", "low", "moderate", "high", "severe"]
CoordinationDecisionType = Literal[
    "prioritize",
    "defer",
    "rebalance",
    "escalate",
    "reduce_reasoning",
    "governance_gate",
    "no_action",
]

# Built-in policy profile names
PolicyProfile = Literal[
    "incident_response",
    "finance",
    "travel_operations",
    "executive_coordination",
    "security_operations",
    "research_analysis",
    "default",
]


class OrganizationalWorkflowContext(BaseModel):
    """Organizational metadata for a single workflow."""
    workflow_id: str
    workflow_domain: str                           # e.g. "travel", "finance", "incident"
    organizational_priority: str = "standard"     # "critical"|"high"|"standard"|"low"|"background"
    operational_criticality: OperationalCriticality = "standard"
    governance_profile: PolicyProfile = "default"
    execution_budget_weight: float = Field(
        default=1.0, ge=0.0, le=5.0,
        description="Relative budget claim vs other workflows (1.0 = normal share).",
    )
    shared_resource_groups: list[str] = Field(
        default_factory=list,
        description="Resource pools this workflow participates in.",
    )
    active: bool = True


class SharedOperationalResource(BaseModel):
    """A pooled resource shared across workflows."""
    resource_id: str
    resource_type: str                             # "reasoning_budget"|"approval_bandwidth"|"delegation_pool"|"optimization_budget"
    total_capacity: float = 1.0                    # normalized 0–1
    active_workflows: list[str] = Field(default_factory=list)
    contention_level: ContentionLevel = "none"
    resource_pressure: float = Field(default=0.0, ge=0.0, le=1.0)
    allocated: dict[str, float] = Field(default_factory=dict)  # workflow_id → share


class OrganizationalPolicy(BaseModel):
    """Governance + execution policy for a workflow domain."""
    policy_name: str
    workflow_domains: list[str]
    governance_level: GovernanceLevel = "standard"
    execution_constraints: dict = Field(default_factory=dict)
    optimization_limits: dict = Field(default_factory=dict)
    reasoning_depth: str = "standard"             # "shallow"|"standard"|"deep"
    clarification_threshold: float = 0.70
    auto_approve: bool = False
    notes: list[str] = Field(default_factory=list)


class WorkflowCoordinationDecision(BaseModel):
    """A coordination action taken by the multi-workflow coordination engine."""
    decision_type: CoordinationDecisionType
    affected_workflows: list[str]
    reason: str
    operational_impact: str
    priority_boost_recipient: str | None = None
    deferral_duration_hint: str | None = None
