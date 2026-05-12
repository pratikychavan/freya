"""freya/equilibrium/rendering.py

Human-centered rendering for the Multi-Equilibrium Operational Cognition Layer.

Style: adaptive, operationally intelligent, executive-friendly.
NOT distributed systems telemetry or orchestration graphs.
"""
from __future__ import annotations

from freya.equilibrium.models import (
    MultiEquilibriumAssessment,
    OperationalEquilibriumZone,
    ZonePropagationEffect,
    ZoneRecoveryPlan,
)


def render_zone_state(zone: OperationalEquilibriumZone) -> str:
    """Render a single zone's current equilibrium state."""
    state_labels = {
        "unstable":    "UNSTABLE — active stabilization required",
        "recovering":  "Recovering — stabilization in progress",
        "stabilized":  "Stabilized — within safe operating bounds",
        "restored":    "Restored — full operational baseline",
    }
    active_label = "Active" if zone.stabilization_active else "None"
    lines = [
        f"  {zone.zone_name}",
        f"    State:               {state_labels.get(zone.equilibrium_state, zone.equilibrium_state)}",
        f"    Pressure:            {zone.pressure_level:.0%}",
        f"    Stabilization:       {active_label}",
        f"    Recovery stage:      {zone.recovery_stage.replace('_', ' ').title()}",
    ]
    return "\n".join(lines)


def render_cross_zone_propagation(effects: list[ZonePropagationEffect]) -> str:
    """Render cross-zone propagation effects as an executive causal summary."""
    if not effects:
        return (
            "┌─ Cross-Zone Propagation ────────────────────────────────────────────┐\n"
            "│  No active cross-zone propagation detected.\n"
            "└─────────────────────────────────────────────────────────────────────┘"
        )
    severity_icons = {"low": "·", "moderate": "▲", "high": "▲▲"}
    lines = [
        "┌─ Cross-Zone Propagation ────────────────────────────────────────────┐",
    ]
    for effect in effects:
        icon = severity_icons.get(effect.severity, "·")
        lines.append(f"│  {icon}  {effect.source_zone}  →  {effect.target_zone}  [{effect.severity.upper()}]")
        lines.append(f"│     {effect.propagation_effect}")
        lines.append(f"│     Impact: {effect.stabilization_impact}")
        lines.append("│")
    lines[-1] = "└─────────────────────────────────────────────────────────────────────┘"
    return "\n".join(lines)


def render_recovery_plan(plan: ZoneRecoveryPlan) -> str:
    """Render a zone recovery plan as a bounded restoration strategy."""
    risk_labels = {
        "low":      "Low",
        "moderate": "Moderate — pacing validation recommended",
        "high":     "HIGH — conservative pacing mandatory",
    }
    lines = [
        f"┌─ Recovery Plan: {plan.zone_name} {'─' * max(0, 55 - len(plan.zone_name))}┐",
        f"│  Pacing:    {plan.pacing_strategy}",
        f"│  Timeline:  {plan.projected_recovery_window}",
        f"│  Rebound:   {risk_labels.get(plan.rebound_risk, plan.rebound_risk)}",
        "│",
        "│  Actions:",
    ]
    for action in plan.restoration_actions:
        lines.append(f"│    • {action}")
    lines.append("└─────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_multi_equilibrium_summary(
    assessment: MultiEquilibriumAssessment,
    zones: dict[str, OperationalEquilibriumZone],
    balancing_recommendations: list[dict] | None = None,
) -> str:
    """Render a partition-aware executive multi-equilibrium summary."""
    stability_labels = {
        "critical":    "CRITICAL — immediate response required",
        "unstable":    "Unstable — active stabilization needed across zones",
        "mixed":       "Mixed — partial stabilization; monitoring required",
        "stabilizing": "Stabilizing — positive trajectory; continue current pacing",
        "stable":      "Stable — all zones within safe operating bounds",
    }
    risk_labels = {
        "low":      "Low",
        "moderate": "Moderate",
        "high":     "High",
        "critical": "CRITICAL",
    }

    lines = [
        "┌─ Multi-Equilibrium Operational Summary ─────────────────────────────┐",
        f"│  Global Stability:     {stability_labels.get(assessment.global_stability, assessment.global_stability)}",
        f"│  Coordination Risk:    {risk_labels.get(assessment.coordination_risk, assessment.coordination_risk)}",
        "│",
    ]

    if assessment.unstable_zones:
        lines.append("│  Unstable Zones:")
        for name in assessment.unstable_zones:
            lines.append(f"│    ✗  {name}")
        lines.append("│")

    if assessment.recovering_zones:
        lines.append("│  Recovering Zones:")
        for name in assessment.recovering_zones:
            lines.append(f"│    ▲  {name}")
        lines.append("│")

    if assessment.stabilized_zones:
        lines.append("│  Stabilized Zones:")
        for name in assessment.stabilized_zones:
            lines.append(f"│    ✓  {name}")
        lines.append("│")

    # Per-zone pressure summary
    lines.append("│  Zone Pressure Overview:")
    for zone in zones.values():
        bar = "█" * int(zone.pressure_level * 10) + "░" * (10 - int(zone.pressure_level * 10))
        lines.append(f"│    {zone.zone_name:<22} {bar} {zone.pressure_level:.0%}")
    lines.append("│")

    # Balancing recommendations
    if balancing_recommendations:
        lines.append("│  Balancing Recommendations:")
        for rec in balancing_recommendations:
            lines.append(f"│    → {rec['balancing_action']}")
        lines.append("│")

    # Coordination outlook
    if assessment.global_stability in ("stable", "stabilizing"):
        outlook = "Global equilibrium improving. Continue current recovery pacing."
    elif assessment.global_stability == "mixed":
        primary_risk = assessment.unstable_zones[0] if assessment.unstable_zones else "unidentified zone"
        outlook = f"Partial stability achieved. {primary_risk} remains the primary risk area."
    else:
        outlook = (
            f"{len(assessment.unstable_zones)} zone(s) require active stabilization. "
            "Recovery must proceed asymmetrically to avoid synchronized rebound."
        )
    lines.append(f"│  Coordination Outlook: {outlook}")
    lines.append("└─────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)
