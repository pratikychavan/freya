"""freya/partitioning/rendering.py

Human-centered rendering for the Adaptive Organizational Partitioning Layer.

Style: adaptive, strategically coordinated, operationally intelligent, executive-friendly.
NOT self-organizing AI theater or graph clustering telemetry.
"""
from __future__ import annotations

from freya.partitioning.models import (
    OperationalPartition,
    OperationalSustainabilityAssessment,
    PartitionCouplingState,
    PressureMigrationEvent,
)


def render_operational_partition(partition: OperationalPartition) -> str:
    """Render a single operational partition as a bounded coordination summary."""
    priority_labels = {
        "critical": "CRITICAL — immediate stabilization required",
        "high":     "High — elevated stabilization priority",
        "moderate": "Moderate — contained within normal bounds",
        "low":      "Low — monitoring only",
    }
    lines = [
        f"┌─ Partition: {partition.partition_name} {'─' * max(0, 56 - len(partition.partition_name))}┐",
        f"│  Type:      {partition.partition_type.replace('_', ' ').title()}",
        f"│  Priority:  {priority_labels.get(partition.stabilization_priority, partition.stabilization_priority)}",
        f"│  Pressure:  {partition.dominant_pressure}",
        "│",
        "│  Participating Workflows:",
    ]
    for wf in partition.participating_workflows:
        lines.append(f"│    • {wf.replace('_', ' ')}")
    lines.append("└─────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_pressure_migration(event: PressureMigrationEvent) -> str:
    """Render a pressure migration event as an operational handoff narrative."""
    lines = [
        "┌─ Pressure Migration Event ──────────────────────────────────────────┐",
        f"│  From:        {event.source_partition}",
        f"│  To:          {event.target_partition}",
        f"│  Confidence:  {event.confidence_score:.0%}",
        "│",
        "│  Migration Reason:",
        f"│    {event.migration_reason}",
        "│",
        "│  Projected Effect:",
        f"│    {event.projected_operational_effect}",
        "└─────────────────────────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


def render_partition_coupling(coupling: PartitionCouplingState) -> str:
    """Render a partition coupling state as an organizational dependency summary."""
    strength_labels = {
        "tight":    "Tight — high mutual influence; destabilization propagates readily",
        "moderate": "Moderate — partial influence; managed propagation risk",
        "loose":    "Loose — limited influence; propagation damped",
        "isolated": "Isolated — no active coupling pathway",
    }
    risk_icons = {"low": "·", "moderate": "▲", "high": "▲▲"}
    lines = [
        "┌─ Partition Coupling ────────────────────────────────────────────────┐",
        f"│  {coupling.source_partition}",
        f"│    ↕ {strength_labels.get(coupling.coupling_strength, coupling.coupling_strength)}",
        f"│  {coupling.target_partition}",
        f"│  Propagation risk: {risk_icons.get(coupling.propagation_risk, '?')} {coupling.propagation_risk.upper()}",
        "│",
        f"│  Dependency: {coupling.stabilization_dependency}",
        "└─────────────────────────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


def render_sustainability_assessment(assessment: OperationalSustainabilityAssessment) -> str:
    """Render a sustainability assessment as an executive operational health summary."""
    state_labels = {
        "sustainable": "Sustainable — strategy within long-term capacity bounds",
        "at_risk":     "At Risk — early fatigue signal; rotation planning recommended",
        "fatigued":    "Fatigued — intervention effectiveness declining",
        "exhausted":   "EXHAUSTED — organizational capacity critically depleted",
    }
    fatigue_labels = {
        "low":      "Low",
        "moderate": "Moderate — monitor closely",
        "high":     "High — rotation required soon",
        "critical": "CRITICAL — immediate rotation required",
    }
    lines = [
        "┌─ Operational Sustainability Assessment ─────────────────────────────┐",
        f"│  Sustainability State:  {state_labels.get(assessment.sustainability_state, assessment.sustainability_state)}",
        f"│  Fatigue Risk:          {fatigue_labels.get(assessment.adaptation_fatigue_risk, assessment.adaptation_fatigue_risk)}",
        "│",
    ]
    if assessment.overloaded_partitions:
        lines.append("│  Overloaded Partitions:")
        for name in assessment.overloaded_partitions:
            lines.append(f"│    ⚠  {name}")
        lines.append("│")
    lines.append(f"│  Recovery Sustainability: {assessment.recovery_sustainability}")
    lines.append("│")
    lines.append(f"│  Organizational Outlook: {assessment.organizational_outlook}")
    lines.append("└─────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)
