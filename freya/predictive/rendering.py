"""freya/predictive/rendering.py

Human-readable rendering for the Predictive Operational Coordination layer.
Style: anticipatory, executive-friendly, stabilizing. No AI theatrics.
"""
from __future__ import annotations

from freya.predictive.models import (
    EquilibriumAssessment,
    OperationalForecast,
    OperationalReservation,
    PredictiveAdjustmentPlan,
    RecoveryForecast,
)


def render_operational_forecast(forecast: OperationalForecast) -> str:
    """Render a forecast as an executive-friendly coordination update."""
    confidence_label = {
        "confirmed":   "Confirmed",
        "high":        "High",
        "moderate":    "Moderate",
        "low":         "Indicative",
        "speculative": "Speculative — monitoring only",
    }.get(forecast.confidence_tier, forecast.confidence_tier.title())

    lines = [
        "┌─ Operational Forecast ──────────────────────────────────────────────┐",
        f"│  Forecast ID:      {forecast.forecast_id}",
        f"│  Window:           {forecast.forecast_window_minutes} minutes",
        f"│  Confidence:       {forecast.confidence_score:.0%}  ({confidence_label})",
        "│",
        f"│  Pressure outlook:     {forecast.predicted_pressure_level.upper()}",
        f"│  Governance load:      {forecast.predicted_governance_load.replace('_', ' ').upper()}",
        f"│  Contention risk:      {forecast.predicted_contention_risk.upper()}",
        "│",
        "│  Contributing signals:",
    ]
    for sig in forecast.contributing_signals:
        lines.append(f"│    • {sig.replace('_', ' ').title()}")
    lines.append("│")
    action = "Preventive action recommended." if forecast.action_warranted else "Observation mode — no action required."
    lines.append(f"│  Status:  {action}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_equilibrium_state(assessment: EquilibriumAssessment) -> str:
    """Render equilibrium state as a coordination briefing."""
    state_labels = {
        "stable":        "Stable",
        "monitoring":    "Monitoring — minor deviations",
        "at_risk":       "At Risk — unfavorable trends",
        "destabilizing": "Destabilizing — active deterioration",
        "critical":      "CRITICAL — immediate action required",
    }
    trend_arrows = {
        "improving":    "↑ Improving",
        "stable":       "→ Stable",
        "declining":    "↓ Declining",
        "deteriorating": "↓↓ Deteriorating",
    }

    lines = [
        "┌─ Equilibrium Assessment ────────────────────────────────────────────┐",
        f"│  State:    {state_labels.get(assessment.equilibrium_state, assessment.equilibrium_state)}",
        f"│  Trend:    {trend_arrows.get(assessment.stability_trend, assessment.stability_trend)}",
        f"│  Risk:     {assessment.projected_disruption_risk.upper()}",
        f"│  Stabilize: {'Recommended' if assessment.stabilization_recommended else 'Not required'}",
        "│",
        "│  Assessment:",
    ]
    for note in assessment.assessment_notes:
        lines.append(f"│    • {note}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_predictive_adjustments(plan: PredictiveAdjustmentPlan) -> str:
    """Render a predictive adjustment plan as a coordination update."""
    phase_label = plan.smoothing_phase.replace("_", " ").title() if plan.smoothing_phase else "Standard"
    lines = [
        "┌─ Predictive Coordination Update ───────────────────────────────────┐",
        f"│  Plan ID:          {plan.plan_id}",
        f"│  Smoothing phase:  {phase_label}",
        f"│  Confidence basis: {plan.confidence_basis:.0%}",
        f"│  Reversible:       {'Yes' if plan.reversibility else 'No'}",
        f"│  Gov. risk:        {plan.governance_risk.upper()}",
        "│",
        "│  Preventive Actions:",
    ]
    for adj in plan.proactive_adjustments:
        lines.append(f"│    • {adj}")
    lines.append("│")
    lines.append(f"│  Expected Impact:  {plan.expected_prevention_impact}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_reservation_state(reservations: list[OperationalReservation]) -> str:
    """Render all active reservations in a concise ledger view."""
    if not reservations:
        return (
            "┌─ Reservation Ledger ────────────────────────────────────────────────┐\n"
            "│  No active reservations.                                            │\n"
            "└────────────────────────────────────────────────────────────────────┘"
        )

    lines = [
        "┌─ Reservation Ledger ────────────────────────────────────────────────┐",
    ]
    for r in reservations:
        lines.append(f"│  [{r.reservation_id}]  {r.reserved_resource:<28} {r.reserved_capacity:.0%} reserved")
        lines.append(f"│    For:     {r.protected_for_workflow}")
        lines.append(f"│    Reason:  {r.reservation_reason}")
        lines.append(f"│    Expiry:  {r.expiration_condition}")
        lines.append("│")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_recovery_forecast(forecast: RecoveryForecast) -> str:
    """Render a recovery forecast as a coordination outlook."""
    lines = [
        "┌─ Recovery Forecast ──────────────────────────────────────────────────┐",
        f"│  Estimated recovery:    ~{forecast.estimated_recovery_minutes} minutes",
        f"│  Likelihood:            {forecast.recovery_likelihood:.0%}",
        f"│  Reservation release:   {forecast.reservation_release_trigger}",
        "│  Notes:",
    ]
    for note in forecast.recovery_notes:
        lines.append(f"│    • {note}")
    lines.append("└─────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_full_predictive_state(
    forecast: OperationalForecast,
    equilibrium: EquilibriumAssessment,
    adjustment_plans: list[PredictiveAdjustmentPlan],
    reservations: list[OperationalReservation],
    recovery: RecoveryForecast | None = None,
) -> str:
    sections = [
        "═" * 70,
        "  PREDICTIVE OPERATIONAL COORDINATION — CYCLE REPORT",
        "═" * 70,
        "",
        render_operational_forecast(forecast),
        "",
        render_equilibrium_state(equilibrium),
    ]

    if adjustment_plans:
        sections.append("\n── Preventive Adjustments ──")
        for plan in adjustment_plans:
            sections.append(render_predictive_adjustments(plan))

    if reservations:
        sections.append("\n── Capacity Reservations ──")
        sections.append(render_reservation_state(reservations))

    if recovery:
        sections.append("\n── Recovery Outlook ──")
        sections.append(render_recovery_forecast(recovery))

    sections.append("═" * 70)
    return "\n".join(sections)
