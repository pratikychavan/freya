"""freya/strategic_governance/rendering.py

Human-centered rendering for the strategic governance cognition layer.

Outputs are executive-friendly, context-aware, and continuity-preserving —
not optimization dashboards or opaque scoring readouts.
"""
from __future__ import annotations

from freya.strategic_governance.models import (
    GovernanceSustainabilityState,
    ResilienceElasticityAssessment,
    StrategicContinuityForecast,
    StrategicGovernancePriority,
)


def _box(title: str, lines: list[str]) -> str:
    width = max(len(title), *(len(l) for l in lines), 50) + 4
    border = "─" * width
    rows = [f"┌{border}┐", f"│  {title.upper():<{width - 2}}│"]
    rows.append(f"├{border}┤")
    for line in lines:
        rows.append(f"│  {line:<{width - 2}}│")
    rows.append(f"└{border}┘")
    return "\n".join(rows)


def render_strategic_priorities(priority: StrategicGovernancePriority) -> str:
    lines = [
        f"Context          : {priority.context_name.upper()}",
        "",
        "Prioritized Characteristics:",
    ]
    for c in priority.prioritized_characteristics:
        lines.append(f"  ↑ {c.replace('_', ' ')}")
    if priority.temporarily_deprioritized:
        lines.append("")
        lines.append("Temporarily Deprioritized:")
        for c in priority.temporarily_deprioritized:
            lines.append(f"  ↓ {c.replace('_', ' ')} (temporary)")
    lines.append("")
    lines.append("Governance Constraints:")
    for constraint in priority.governance_constraints:
        for i in range(0, len(constraint), 74):
            prefix = "  — " if i == 0 else "    "
            lines.append(f"{prefix}{constraint[i:i+74]}")
    lines.append("")
    lines.append("Rationale:")
    for i in range(0, len(priority.rationale), 76):
        lines.append(f"  {priority.rationale[i:i+76]}")
    return _box(f"Strategic Priority Profile — {priority.context_name}", lines)


def render_elasticity_assessment(assessment: ResilienceElasticityAssessment) -> str:
    load_pct = f"{assessment.current_load:.0%}"
    threshold_pct = f"{assessment.elasticity_threshold:.0%}"
    headroom = max(0.0, assessment.elasticity_threshold - assessment.current_load)
    lines = [
        f"Domain           : {assessment.elasticity_domain.upper()}",
        f"Current Load     : {load_pct}",
        f"Threshold        : {threshold_pct}",
        f"Headroom         : {headroom:.0%}",
        f"Failure Risk     : {assessment.projected_failure_risk.upper()}",
        "",
        "Preventive Action:",
    ]
    for i in range(0, len(assessment.preventive_action), 76):
        lines.append(f"  {assessment.preventive_action[i:i+76]}")
    return _box(f"Elasticity Assessment — {assessment.elasticity_domain}", lines)


def render_governance_sustainability(state: GovernanceSustainabilityState) -> str:
    lines = [
        f"Capacity State   : {state.governance_capacity_state.upper()}",
        f"Review Pressure  : {state.review_pressure.upper()}",
        f"Escalation Risk  : {state.escalation_saturation_risk.upper()}",
        f"Sustainability   : {state.sustainability_outlook.upper()}",
        "",
        "Recommended Adjustment:",
    ]
    for i in range(0, len(state.recommended_adjustment), 76):
        lines.append(f"  {state.recommended_adjustment[i:i+76]}")
    return _box("Governance Sustainability State", lines)


def render_strategic_forecast(forecast: StrategicContinuityForecast) -> str:
    confidence_pct = f"{forecast.confidence_score:.0%}"
    lines = [
        f"Horizon          : {forecast.forecast_horizon}",
        f"Confidence       : {confidence_pct}",
        "",
        "Protected Characteristics:",
    ]
    for c in forecast.protected_operational_characteristics:
        lines.append(f"  ✓ {c.replace('_', ' ')}")
    lines.append("")
    lines.append("Anticipated Risks:")
    for risk in forecast.anticipated_risks:
        for i in range(0, len(risk), 74):
            prefix = "  ⚠ " if i == 0 else "    "
            lines.append(f"{prefix}{risk[i:i+74]}")
    lines.append("")
    lines.append("Continuity Strategy:")
    for i in range(0, len(forecast.continuity_strategy), 76):
        lines.append(f"  {forecast.continuity_strategy[i:i+76]}")
    return _box("Strategic Continuity Forecast", lines)
