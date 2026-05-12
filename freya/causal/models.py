"""freya/causal/models.py

Data models for the Causal Operational Reasoning layer.

Design rules:
  - All causal reasoning is bounded to operational telemetry
  - Propagation chains are auditable and explainable
  - Confidence levels drive reasoning depth and recommendation urgency
  - Governance guarantees are never reasoned away
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ── Literals ───────────────────────────────────────────────────────────────────

EventSeverity      = Literal["low", "moderate", "elevated", "high", "critical"]
EquilibriumRisk    = Literal["none", "low", "moderate", "high", "imminent"]
PropagationStrength = Literal["dampened", "neutral", "amplified", "cascading"]
StabilizationEffect = Literal["none", "partial", "significant", "strong", "complete"]


# ── Core causal models ─────────────────────────────────────────────────────────

class OperationalCausalEvent(BaseModel):
    """A discrete observed operational event that triggers causal reasoning."""
    event_id:             str
    event_type:           str   # e.g. "governance_congestion", "retry_spike"
    operational_effect:   str   # plain-language description of primary effect
    originating_workflow: str | None = None
    severity:             EventSeverity
    timestamp_label:      str  = "current"


class CausalPropagationChain(BaseModel):
    """A chain of cause-and-effect steps traced from a root event."""
    chain_id:             str
    root_event:           str
    propagation_steps:    list[str]     # ordered plain-language steps
    projected_outcome:    str
    stabilization_effect: StabilizationEffect
    confidence_score:     float = Field(ge=0.0, le=1.0)
    propagation_strength: PropagationStrength = "neutral"


class CausalInterventionImpact(BaseModel):
    """Complete causal impact analysis for a single intervention."""
    intervention_name:          str
    primary_effects:            list[str]
    secondary_effects:          list[str]
    stabilization_contribution: str
    governance_impact:          str
    unintended_consequences:    list[str] = Field(default_factory=list)
    net_stability_delta:        float = Field(ge=-1.0, le=1.0, default=0.0)


class DestabilizationCascade(BaseModel):
    """A detected or projected destabilization cascade."""
    cascade_id:                str
    trigger_event:             str
    projected_cascade_effects: list[str]
    mitigation_recommendations: list[str]
    equilibrium_risk:          EquilibriumRisk
    cascade_depth:             int = Field(ge=1, default=1)
    is_amplifying:             bool = False


class StabilizationPropagation(BaseModel):
    """How a stabilization effect spreads through the operational graph."""
    intervention_name:    str
    primary_stabilization: str
    propagated_benefits:  list[str]
    reinforcement_chain:  list[str]
    durability_estimate:  str
    equilibrium_impact:   StabilizationEffect
