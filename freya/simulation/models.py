"""freya/simulation/models.py

Data models for the Operational Scenario Simulation Layer.

Design rules:
  - All simulations are bounded and operationally grounded
  - Confidence drives recommendation strength (not decoration)
  - Reversibility is a first-class concern
  - Governance guarantees are never simulated away
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ── Literals ───────────────────────────────────────────────────────────────────

InterventionType = Literal[
    "governance_batching",
    "reasoning_compression",
    "workflow_degradation",
    "reservation_reallocation",
    "optimization_suspension",
    "workflow_deferral",
    "no_intervention",
]

OperationalImpact = Literal["minimal", "low", "moderate", "significant", "severe"]
GovernanceEffect  = Literal["none", "positive", "neutral", "negative", "critical"]
RecoveryDifficulty = Literal["immediate", "easy", "moderate", "complex", "irreversible"]
RiskLevel         = Literal["none", "low", "moderate", "high", "critical"]


# ── Core simulation models ─────────────────────────────────────────────────────

class OperationalScenario(BaseModel):
    """A bounded, described intervention scenario for simulation."""
    scenario_id:              str
    scenario_name:            str
    intervention_type:        InterventionType
    intervention_description: str
    affected_workflows:       list[str]
    simulation_window_minutes: int = Field(ge=1, le=120, default=15)


class SimulationOutcome(BaseModel):
    """The projected operational result of running a scenario."""
    scenario_id:                   str
    predicted_operational_impact:  OperationalImpact
    projected_governance_effect:   GovernanceEffect
    projected_recovery_time:       str        # human-readable e.g. "~10 minutes"
    projected_stability_effect:    str        # human-readable description
    confidence_score:              float = Field(ge=0.0, le=1.0)
    reversibility:                 bool  = True
    recovery_difficulty:           RecoveryDifficulty = "easy"
    key_tradeoffs:                 list[str] = Field(default_factory=list)


class CounterfactualComparison(BaseModel):
    """The result of comparing multiple intervention scenarios."""
    baseline_scenario:       str
    compared_scenarios:      list[str]
    recommended_strategy:    str
    recommendation_reason:   str
    organizational_tradeoffs: list[str]
    confidence_score:        float = Field(ge=0.0, le=1.0, default=0.70)


class SimulationRiskAssessment(BaseModel):
    """Governance and operational risk evaluation for a scenario."""
    scenario_id:       str
    governance_risk:   RiskLevel
    operational_risk:  RiskLevel
    coordination_risk: RiskLevel
    explanation:       str
    safe_to_proceed:   bool = True
    blocking_reasons:  list[str] = Field(default_factory=list)


class InterventionEffect(BaseModel):
    """Modelled effect of a single intervention type."""
    intervention_type:       InterventionType
    approval_interrupt_delta: float  # negative = reduction, positive = increase
    reasoning_quality_delta:  float
    latency_delta_minutes:    float
    stability_improvement:    float  # 0–1
    reversibility:            bool
    recovery_difficulty:      RecoveryDifficulty
    side_effects:             list[str] = Field(default_factory=list)
