"""freya/sequencing/rendering.py

Human-centered rendering for the Coordination Sequencing Layer.

Style: strategic, adaptive, executive-friendly, operationally intelligent.
NOT state-machine dumps. NOT orchestration telemetry.
"""
from __future__ import annotations

from freya.sequencing.models import (
    AdaptiveInterventionDecision,
    InterventionSequence,
    RecoveryProgression,
)


def render_coordination_sequence(
    sequence: InterventionSequence,
    phase_descriptions: dict[str, str] | None = None,
) -> str:
    """Render an InterventionSequence as a phased coordination strategy.

    Args:
        sequence: The sequence to render.
        phase_descriptions: Optional mapping of phase_name → bullet summary.
                            If omitted, phase names are rendered as-is.
    """
    _defaults: dict[str, str] = {
        "Retry Stabilization":       "governance batching reducing retry churn",
        "Governance Recovery":       "approval queue backlog clearing progressively",
        "Contention Reduction":      "reasoning pool pressure stabilizing toward threshold",
        "Operational Restoration":   "optimization depth gradually restored at safe pacing",
    }
    descriptions = {**_defaults, **(phase_descriptions or {})}

    lines = [
        "┌─ Adaptive Coordination Sequence ──────────────────────────────────┐",
        f"│  Strategy:    {sequence.sequence_name.replace('_', ' ').title()}",
        f"│  Confidence:  {sequence.confidence_score:.0%}",
        "│",
    ]
    for i, phase in enumerate(sequence.phases, start=1):
        phase_label = phase.replace("_", " ").title()
        bullet = descriptions.get(phase_label, phase_label)
        lines.append(f"│  Phase {i} — {phase_label}")
        lines.append(f"│    • {bullet}")
    lines.append("│")
    lines.append(f"│  Expected Effect:  {sequence.expected_stabilization_effect}")
    lines.append(f"│  Recovery Profile: {sequence.projected_recovery_profile}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_phase_transition(
    from_phase: str,
    to_phase: str,
    assessment: dict,
) -> str:
    """Render a phase transition equilibrium assessment."""
    risk_label = {
        "low": "Low — transition within safe bounds",
        "moderate": "Moderate — pacing adjustment recommended",
        "high": "HIGH — transition premature; consolidate current phase",
    }.get(assessment.get("equilibrium_risk", "moderate"), "Unknown")

    safe_icon = "✓" if assessment.get("safe_to_transition") else "✗"
    lines = [
        "┌─ Phase Transition Assessment ──────────────────────────────────────┐",
        f"│  {from_phase.replace('_', ' ').title()}  →  {to_phase.replace('_', ' ').title()}",
        f"│  Safe to transition: {safe_icon}",
        f"│  Equilibrium risk:   {risk_label}",
        "│",
        f"│  {assessment.get('pacing_recommendation', '')}",
        "│",
        f"│  Reason: {assessment.get('reason', '')}",
        "└────────────────────────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


def render_adaptive_decision(decision: AdaptiveInterventionDecision) -> str:
    """Render an AdaptiveInterventionDecision as an operational recommendation."""
    lines = [
        "┌─ Adaptive Intervention Decision ───────────────────────────────────┐",
        f"│  Active phase:  {decision.current_phase.replace('_', ' ').title()}",
        "│",
        "│  Recommended Action:",
        f"│    → {decision.recommended_next_action}",
        "│",
        f"│  Adaptation Reason:",
        f"│    {decision.adaptation_reason}",
        "│",
        f"│  Equilibrium Effect:",
        f"│    {decision.equilibrium_effect}",
        "└────────────────────────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


def render_recovery_progression(progression: RecoveryProgression) -> str:
    """Render a RecoveryProgression as a phased restoration status."""
    stage_labels = {
        "early_mitigation": "Early Mitigation — stabilization interventions active",
        "stabilized":       "Stabilized — system holding; recovery pending",
        "recovering":       "Recovering — conservative restoration underway",
        "restoring":        "Restoring — near-full restoration in progress",
        "complete":         "Complete — operational baseline restored",
    }
    stage_label = stage_labels.get(progression.recovery_stage, progression.recovery_stage)

    lines = [
        "┌─ Recovery Progression ─────────────────────────────────────────────┐",
        f"│  Stage:       {stage_label}",
        f"│  Confidence:  {progression.stabilization_confidence:.0%}",
        f"│  Timeline:    {progression.projected_recovery_time}",
        "│",
        "│  Restoration Actions:",
    ]
    for action in progression.restoration_actions:
        lines.append(f"│    • {action}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)
