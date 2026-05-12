"""freya/topology/rendering.py

Topology rendering utilities.

Produces human-readable, executive-friendly summaries of topology
patterns, lifecycle states, memory records, and evolution assessments.
"""
from __future__ import annotations

from freya.topology.models import (
    OperationalMemoryRecord,
    OperationalTopologyPattern,
    TopologyEvolutionAssessment,
    TopologyLifecycleState,
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


def render_topology_pattern(pattern: OperationalTopologyPattern) -> str:
    lines = [
        f"Topology         : {pattern.topology_name}",
        f"Recurrence       : {pattern.recurrence_frequency.upper()}",
        f"Org. Impact      : {pattern.organizational_impact}",
    ]
    if pattern.recurring_partitions:
        lines.append(f"Recurring Parts. : {', '.join(pattern.recurring_partitions)}")
    if pattern.recurring_pressure_patterns:
        lines.append(f"Pressure Signals : {', '.join(pattern.recurring_pressure_patterns)}")
    return _box(f"Topology Pattern — {pattern.topology_name}", lines)


def render_lifecycle_state(state: TopologyLifecycleState) -> str:
    dissolution_pct = f"{state.dissolution_probability:.0%}"
    lines = [
        f"Topology         : {state.topology_name}",
        f"Lifecycle Stage  : {state.lifecycle_stage.upper()}",
        f"Dissolution Prob.: {dissolution_pct}",
        f"Stab. Maturity   : {state.stabilization_maturity}",
        f"Evolution Risk   : {state.projected_evolution_risk}",
    ]
    return _box(f"Lifecycle State — {state.topology_name}", lines)


def render_operational_memory(record: OperationalMemoryRecord) -> str:
    lines = [
        f"Pattern          : {record.historical_pattern[:80]}",
    ]
    if len(record.historical_pattern) > 80:
        remainder = record.historical_pattern[80:]
        for i in range(0, len(remainder), 76):
            lines.append(f"                   {remainder[i:i+76]}")
    lines.extend([
        f"Outcome          : {record.stabilization_outcome.upper()}",
        f"Recovery Duration: {record.recovery_duration}",
        "Recommendation   :",
    ])
    for i in range(0, len(record.future_recommendation), 76):
        lines.append(f"  {record.future_recommendation[i:i+76]}")
    return _box("Operational Memory Record", lines)


def render_topology_evolution_summary(assessment: TopologyEvolutionAssessment) -> str:
    confidence_pct = f"{assessment.confidence_score:.0%}"
    lines = [
        f"Evolution State  : {assessment.evolution_state.upper()}",
        f"Instability Risk : {assessment.chronic_instability_risk.upper()}",
        f"Sustainability   : {assessment.sustainability_outlook.upper()}",
        f"Confidence       : {confidence_pct}",
        "Recommended      :",
    ]
    for i in range(0, len(assessment.recommended_adaptation), 76):
        lines.append(f"  {assessment.recommended_adaptation[i:i+76]}")
    return _box("Organizational Topology Evolution Summary", lines)


def render_sustainability_summary(sustainability: dict) -> str:
    lines = [
        f"Sustainability   : {sustainability.get('sustainability_state', 'unknown').upper()}",
        f"Resilience       : {sustainability.get('resilience_outlook', 'unknown').upper()}",
        f"Horizon Cycles   : {sustainability.get('cycle_horizon', '—')}",
        "",
        "Future Risk Factors:",
    ]
    for risk in sustainability.get("future_risk_factors", []):
        for i in range(0, len(risk), 74):
            lines.append(f"  {risk[i:i+74]}")
    lines.append("")
    lines.append("Recommended Rotation:")
    for rec in sustainability.get("recommended_rotation", []):
        for i in range(0, len(rec), 74):
            lines.append(f"  {rec[i:i+74]}")
    return _box("Long-Horizon Sustainability Assessment", lines)
