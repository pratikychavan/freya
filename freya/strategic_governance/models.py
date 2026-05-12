"""freya/strategic_governance/models.py

Data models for the Strategic Organizational Governance Cognition Layer.

All models are Pydantic v2. Represents governance priorities, elasticity
assessments, sustainability states, and continuity forecasts — bounded
and fully explainable.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Literal type aliases
# ---------------------------------------------------------------------------

ProjectedFailureRisk = Literal["low", "moderate", "high", "critical"]
GovernanceCapacityState = Literal["healthy", "strained", "saturated", "critical"]
ReviewPressure = Literal["low", "moderate", "high", "critical"]
EscalationSaturationRisk = Literal["low", "moderate", "high", "critical"]
SustainabilityOutlook = Literal["sustainable", "at_risk", "degrading", "unsustainable"]
OperationalContext = Literal[
    "normal",
    "incident",
    "audit",
    "release_window",
    "migration",
    "governance_review",
]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class StrategicGovernancePriority(BaseModel):
    """Contextual prioritization of organizational characteristics."""

    context_name: str
    prioritized_characteristics: list[str]
    temporarily_deprioritized: list[str]
    governance_constraints: list[str]
    rationale: str


class ResilienceElasticityAssessment(BaseModel):
    """Forecast of an elasticity domain approaching its breaking point."""

    elasticity_domain: str
    current_load: float                    # [0.0, 1.0]
    elasticity_threshold: float            # [0.0, 1.0]
    projected_failure_risk: ProjectedFailureRisk
    preventive_action: str


class GovernanceSustainabilityState(BaseModel):
    """Assessment of governance process sustainability."""

    governance_capacity_state: GovernanceCapacityState
    review_pressure: ReviewPressure
    escalation_saturation_risk: EscalationSaturationRisk
    sustainability_outlook: SustainabilityOutlook
    recommended_adjustment: str


class StrategicContinuityForecast(BaseModel):
    """Forward-looking forecast of organizational continuity risks."""

    forecast_horizon: str
    protected_operational_characteristics: list[str]
    anticipated_risks: list[str]
    continuity_strategy: str
    confidence_score: float                # [0.0, 1.0]
