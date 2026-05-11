"""freya/predictive/equilibrium.py

OperationalEquilibriumEngine

Assesses organizational equilibrium and detects early destabilization trends.
Recommendations are bounded and explainable — no opaque AI decisions.

Equilibrium states (from stable → critical):
  stable          — system healthy, no action required
  monitoring      — slight deviations, watch closely
  at_risk         — trends suggest future instability
  destabilizing   — active deterioration, proactive stabilization warranted
  critical        — immediate coordinated response required
"""
from __future__ import annotations

from freya.predictive.models import (
    DisruptionRisk,
    EquilibriumAssessment,
    EquilibriumState,
    OperationalForecast,
    OperationalSignal,
    StabilityTrend,
)

# ── State classification ───────────────────────────────────────────────────────

def _equilibrium_state(
    rising_fraction: float,
    max_severity: float,
    avg_severity: float,
) -> EquilibriumState:
    if max_severity >= 0.85 or avg_severity >= 0.70:
        return "critical"
    if rising_fraction >= 0.65 or avg_severity >= 0.55:
        return "destabilizing"
    if rising_fraction >= 0.40 or avg_severity >= 0.35:
        return "at_risk"
    if rising_fraction >= 0.20 or avg_severity >= 0.20:
        return "monitoring"
    return "stable"


def _stability_trend(
    rising_fraction: float,
    falling_fraction: float,
) -> StabilityTrend:
    if rising_fraction >= 0.60:
        return "deteriorating"
    if rising_fraction >= 0.35:
        return "declining"
    if falling_fraction >= 0.40:
        return "improving"
    return "stable"


def _disruption_risk(
    forecast: OperationalForecast | None,
    avg_severity: float,
) -> DisruptionRisk:
    pressure_ranks = {"low": 0, "moderate": 1, "elevated": 2, "high": 3, "critical": 4}
    forecast_rank  = pressure_ranks.get(
        forecast.predicted_pressure_level if forecast else "low", 0
    )

    combined = (avg_severity * 0.6) + (forecast_rank / 4.0 * 0.4)
    if combined >= 0.80:  return "imminent"
    if combined >= 0.60:  return "high"
    if combined >= 0.40:  return "moderate"
    if combined >= 0.20:  return "low"
    return "none"


# ── Assessment notes ────────────────────────────────────────────────────────────

_STATE_NOTES: dict[EquilibriumState, list[str]] = {
    "stable":        ["No destabilization indicators. Operational equilibrium maintained."],
    "monitoring":    ["Minor signal deviations detected. Continuing routine observation."],
    "at_risk":       [
        "Multiple signals trending unfavorably.",
        "Proactive monitoring recommended.",
        "Consider pre-batching governance reviews.",
    ],
    "destabilizing": [
        "Active destabilization trend detected.",
        "Proactive stabilization recommended.",
        "Gradually compress low-priority workloads.",
        "Reserve reasoning capacity for incident workflows.",
    ],
    "critical":      [
        "Critical equilibrium breach detected.",
        "Immediate coordinated stabilization required.",
        "Apply emergency smoothing across all non-critical workflows.",
        "Governance reviews must be batched immediately.",
    ],
}


class OperationalEquilibriumEngine:
    """Assess organizational equilibrium and recommend stabilization."""

    def assess(
        self,
        signals: list[OperationalSignal],
        forecast: OperationalForecast | None = None,
    ) -> EquilibriumAssessment:
        if not signals:
            return EquilibriumAssessment(
                equilibrium_state="stable",
                stability_trend="stable",
                projected_disruption_risk="none",
                stabilization_recommended=False,
                assessment_notes=["No signals available — defaulting to stable."],
            )

        total          = len(signals)
        rising         = sum(1 for s in signals if s.direction == "rising")
        falling        = sum(1 for s in signals if s.direction == "falling")
        rising_frac    = rising / total
        falling_frac   = falling / total
        avg_severity   = sum(s.severity for s in signals) / total
        max_severity   = max(s.severity for s in signals)

        state   = _equilibrium_state(rising_frac, max_severity, avg_severity)
        trend   = _stability_trend(rising_frac, falling_frac)
        risk    = _disruption_risk(forecast, avg_severity)
        notes   = list(_STATE_NOTES.get(state, []))

        # Add forecast context
        if forecast and forecast.action_warranted:
            notes.append(
                f"Forecast ({forecast.forecast_window_minutes}min): "
                f"pressure={forecast.predicted_pressure_level}, "
                f"governance={forecast.predicted_governance_load}, "
                f"confidence={forecast.confidence_score:.0%}."
            )

        return EquilibriumAssessment(
            equilibrium_state=state,
            stability_trend=trend,
            projected_disruption_risk=risk,
            stabilization_recommended=state in ("at_risk", "destabilizing", "critical"),
            assessment_notes=notes,
        )

    def severity_score(self, assessment: EquilibriumAssessment) -> float:
        """Return a 0–1 numeric score representing equilibrium health."""
        state_scores: dict[EquilibriumState, float] = {
            "stable":        0.0,
            "monitoring":    0.2,
            "at_risk":       0.4,
            "destabilizing": 0.7,
            "critical":      1.0,
        }
        return state_scores.get(assessment.equilibrium_state, 0.0)
