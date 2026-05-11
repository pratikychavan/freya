"""freya/predictive/models.py

Data models for the Predictive Operational Coordination layer.

Design rules:
  - All forecasts are bounded and operationally grounded
  - Confidence levels drive action aggressiveness (not decoration)
  - All reservations expire; no permanent capacity hoarding
  - Adjustments are gradual and reversible
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ── Literals ───────────────────────────────────────────────────────────────────

PressureLevel       = Literal["low", "moderate", "elevated", "high", "critical"]
GovernanceLoad      = Literal["normal", "increasing", "elevated", "congested", "overloaded"]
ContentionRisk      = Literal["none", "low", "moderate", "high", "severe"]
EquilibriumState    = Literal["stable", "monitoring", "at_risk", "destabilizing", "critical"]
StabilityTrend      = Literal["improving", "stable", "declining", "deteriorating"]
DisruptionRisk      = Literal["none", "low", "moderate", "high", "imminent"]
ConfidenceTier      = Literal["speculative", "low", "moderate", "high", "confirmed"]
SmoothingPhase      = Literal["none", "gentle", "moderate", "aggressive", "emergency"]
SignalDirection      = Literal["stable", "rising", "falling", "volatile"]


# ── Core predictive models ─────────────────────────────────────────────────────

class OperationalForecast(BaseModel):
    """A bounded, explainable forecast of near-term operational state."""
    forecast_id:               str
    forecast_window_minutes:   int   = Field(ge=1, le=60)
    predicted_pressure_level:  PressureLevel
    predicted_governance_load: GovernanceLoad
    predicted_contention_risk: ContentionRisk
    confidence_score:          float = Field(ge=0.0, le=1.0)
    contributing_signals:      list[str]

    @property
    def confidence_tier(self) -> ConfidenceTier:
        if self.confidence_score >= 0.85:
            return "confirmed"
        if self.confidence_score >= 0.70:
            return "high"
        if self.confidence_score >= 0.50:
            return "moderate"
        if self.confidence_score >= 0.30:
            return "low"
        return "speculative"

    @property
    def action_warranted(self) -> bool:
        """True when confidence is sufficient to take preventive action."""
        return self.confidence_score >= 0.50


class EquilibriumAssessment(BaseModel):
    """Snapshot of current organizational equilibrium and trend."""
    equilibrium_state:        EquilibriumState
    stability_trend:          StabilityTrend
    projected_disruption_risk: DisruptionRisk
    stabilization_recommended: bool
    assessment_notes:         list[str] = Field(default_factory=list)


class OperationalReservation(BaseModel):
    """A proactive capacity reservation for a protected workflow."""
    reservation_id:        str
    reserved_resource:     str
    reserved_capacity:     float = Field(ge=0.0, le=1.0)
    protected_for_workflow: str
    reservation_reason:    str
    expiration_condition:  str
    active:                bool = True


class PredictiveAdjustmentPlan(BaseModel):
    """A set of proactive, gradual adjustments to prevent instability."""
    plan_id:                   str
    proactive_adjustments:     list[str]
    expected_prevention_impact: str
    governance_risk:           str = "none"
    reversibility:             bool = True
    smoothing_phase:           SmoothingPhase = "none"
    confidence_basis:          float = Field(ge=0.0, le=1.0, default=0.70)


class OperationalSignal(BaseModel):
    """A single observed operational telemetry signal."""
    signal_name:    str
    current_value:  float
    baseline_value: float
    direction:      SignalDirection
    severity:       float = Field(ge=0.0, le=1.0)  # 0=no concern, 1=critical
    description:    str

    @property
    def deviation(self) -> float:
        if self.baseline_value == 0.0:
            return 0.0
        return (self.current_value - self.baseline_value) / self.baseline_value


class RecoveryForecast(BaseModel):
    """Forecast of when and how the system will recover from pressure."""
    estimated_recovery_minutes: int
    recovery_likelihood:        float = Field(ge=0.0, le=1.0)
    recovery_notes:             list[str] = Field(default_factory=list)
    reservation_release_trigger: str = "pressure_normalized"
