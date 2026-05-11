"""freya/predictive/forecasting.py

OperationalForecastingEngine

Converts operational signals into bounded, explainable forecasts.
Forecasting is deterministic and telemetry-driven — no speculative AI.

Forecast confidence drives action:
  confirmed / high  → proactive reservations + smoothing active
  moderate          → early monitoring + gentle smoothing
  low / speculative → observe only; no preemptive changes
"""
from __future__ import annotations

import uuid

from freya.predictive.models import (
    ContentionRisk,
    GovernanceLoad,
    OperationalForecast,
    OperationalSignal,
    PressureLevel,
    RecoveryForecast,
)

# ── Pressure classification ────────────────────────────────────────────────────

def _classify_pressure(score: float) -> PressureLevel:
    if score >= 0.85:  return "critical"
    if score >= 0.70:  return "high"
    if score >= 0.50:  return "elevated"
    if score >= 0.30:  return "moderate"
    return "low"


def _classify_governance_load(
    escalation_severity: float,
    approval_latency_severity: float,
) -> GovernanceLoad:
    combined = (escalation_severity + approval_latency_severity) / 2.0
    if combined >= 0.80:  return "overloaded"
    if combined >= 0.60:  return "congested"
    if combined >= 0.40:  return "elevated"
    if combined >= 0.20:  return "increasing"
    return "normal"


def _classify_contention(
    degradation_severity: float,
    surge_severity: float,
) -> ContentionRisk:
    combined = (degradation_severity + surge_severity) / 2.0
    if combined >= 0.80:  return "severe"
    if combined >= 0.60:  return "high"
    if combined >= 0.40:  return "moderate"
    if combined >= 0.20:  return "low"
    return "none"


def _forecast_confidence(
    signals: list[OperationalSignal],
    window_minutes: int,
) -> float:
    """Confidence decreases as window grows and as signal count shrinks."""
    if not signals:
        return 0.20
    rising_fraction = sum(1 for s in signals if s.direction == "rising") / len(signals)
    base_confidence = 0.40 + rising_fraction * 0.45
    # Longer windows are less certain
    window_penalty  = min((window_minutes - 5) * 0.015, 0.25)
    return round(max(0.10, base_confidence - window_penalty), 2)


class OperationalForecastingEngine:
    """Produce bounded operational forecasts from aggregated signals."""

    def forecast(
        self,
        signals: list[OperationalSignal],
        window_minutes: int = 15,
    ) -> OperationalForecast:
        """Forecast the operational state within the given time window."""
        signal_map = {s.signal_name: s for s in signals}

        def sev(name: str) -> float:
            return signal_map[name].severity if name in signal_map else 0.0

        overall_pressure = sum(s.severity for s in signals) / len(signals) if signals else 0.0

        pressure_level   = _classify_pressure(overall_pressure)
        governance_load  = _classify_governance_load(
            sev("escalation_frequency"), sev("approval_latency")
        )
        contention_risk  = _classify_contention(
            sev("degradation_usage"), sev("workflow_surge_index")
        )
        confidence       = _forecast_confidence(signals, window_minutes)

        contributing = [
            s.signal_name.replace("_", " ") for s in signals
            if s.direction in ("rising", "volatile") and s.severity >= 0.20
        ]
        if not contributing:
            contributing = ["no significant trends detected"]

        return OperationalForecast(
            forecast_id=str(uuid.uuid4())[:8],
            forecast_window_minutes=window_minutes,
            predicted_pressure_level=pressure_level,
            predicted_governance_load=governance_load,
            predicted_contention_risk=contention_risk,
            confidence_score=confidence,
            contributing_signals=contributing,
        )

    def recovery_forecast(
        self,
        current_pressure: float,
        active_signal_count: int,
        trend: str = "stable",
    ) -> RecoveryForecast:
        """Estimate how soon operational recovery is likely."""
        if trend == "improving" or current_pressure <= 0.30:
            minutes   = max(5, int(current_pressure * 20))
            likelihood = 0.85
        elif trend == "stable":
            minutes   = max(10, int(current_pressure * 40))
            likelihood = 0.65
        else:
            minutes   = max(20, int(current_pressure * 60))
            likelihood = 0.40

        # More active signals → longer recovery
        minutes += active_signal_count * 2

        notes = [
            f"Recovery window: ~{minutes} minutes.",
            f"Recovery likelihood: {likelihood:.0%}.",
        ]
        if current_pressure >= 0.70:
            notes.append("Sustained pressure may delay full restoration.")

        return RecoveryForecast(
            estimated_recovery_minutes=minutes,
            recovery_likelihood=likelihood,
            recovery_notes=notes,
            reservation_release_trigger="pressure_normalized",
        )
