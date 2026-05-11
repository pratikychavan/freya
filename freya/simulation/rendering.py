"""freya/simulation/rendering.py

Human-readable rendering for the Operational Scenario Simulation layer.
Style: strategic, executive-friendly, explainable. No AI roleplay.
"""
from __future__ import annotations

from freya.simulation.models import (
    CounterfactualComparison,
    OperationalScenario,
    SimulationOutcome,
    SimulationRiskAssessment,
)


def render_simulation_scenario(scenario: OperationalScenario) -> str:
    """Render a scenario description."""
    lines = [
        "┌─ Operational Scenario ──────────────────────────────────────────────┐",
        f"│  ID:          {scenario.scenario_id}",
        f"│  Name:        {scenario.scenario_name}",
        f"│  Type:        {scenario.intervention_type.replace('_', ' ').title()}",
        f"│  Window:      {scenario.simulation_window_minutes} minutes",
        f"│  Workflows:   {', '.join(scenario.affected_workflows) or 'All applicable'}",
        "│",
        f"│  Description: {scenario.intervention_description}",
        "└────────────────────────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


def render_simulation_outcome(
    scenario: OperationalScenario, outcome: SimulationOutcome
) -> str:
    """Render the projected outcome of a simulated intervention."""
    rev_label = "Yes" if outcome.reversibility else "No"
    lines = [
        f"  Scenario: {scenario.scenario_name}",
        f"  ─────────────────────────────────────────────────────",
        f"  Operational impact:   {outcome.predicted_operational_impact.upper()}",
        f"  Governance effect:    {outcome.projected_governance_effect.upper()}",
        f"  Recovery time:        {outcome.projected_recovery_time}",
        f"  Reversible:           {rev_label}",
        f"  Confidence:           {outcome.confidence_score:.0%}",
        f"  {outcome.projected_stability_effect}",
    ]
    if outcome.key_tradeoffs:
        lines.append("  Tradeoffs:")
        for t in outcome.key_tradeoffs:
            lines.append(f"    • {t}")
    return "\n".join(lines)


def render_counterfactual_comparison(comparison: CounterfactualComparison) -> str:
    """Render a side-by-side counterfactual comparison result."""
    lines = [
        "┌─ Counterfactual Comparison ─────────────────────────────────────────┐",
        f"│  Baseline:     {comparison.baseline_scenario}",
        f"│  Compared:     {', '.join(comparison.compared_scenarios)}",
        "│",
        f"│  Recommended:  {comparison.recommended_strategy}",
        "│",
        f"│  Reason: {comparison.recommendation_reason}",
        "│",
        "│  Organizational Tradeoffs:",
    ]
    for t in comparison.organizational_tradeoffs:
        lines.append(f"│    • {t}")
    lines.append(f"│  Confidence:   {comparison.confidence_score:.0%}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_strategy_recommendation(
    ranked_summaries: list[dict],
    recommended_name: str,
    reason: str,
) -> str:
    """Render a strategy comparison table with recommendation."""
    lines = [
        "┌─ Strategy Comparison ───────────────────────────────────────────────┐",
        "│  Rank  Strategy                     Score   Impact       Gov.Effect  │",
        "│  ────  ──────────────────────────   ─────   ──────────   ──────────  │",
    ]
    for row in ranked_summaries:
        name   = row["scenario"][:28].ljust(28)
        score  = f"{row['score']:.2f}".rjust(5)
        impact = row["impact"][:10].ljust(10)
        gov    = row["governance"][:10].ljust(10)
        rank   = str(row["rank"]).rjust(4)
        lines.append(f"│  {rank}  {name}   {score}   {impact}   {gov}  │")
    lines.append("│")
    lines.append(f"│  Recommended: {recommended_name}")
    lines.append(f"│  Reason:      {reason}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_risk_assessment(risk: SimulationRiskAssessment) -> str:
    """Render a governance risk assessment for a simulated scenario."""
    status = "✓ SAFE TO SIMULATE" if risk.safe_to_proceed else "✗ BLOCKED"
    lines = [
        "┌─ Risk Assessment ───────────────────────────────────────────────────┐",
        f"│  Scenario:   {risk.scenario_id}",
        f"│  Status:     {status}",
        f"│  Gov. risk:  {risk.governance_risk.upper()}",
        f"│  Op. risk:   {risk.operational_risk.upper()}",
        f"│  Coord. risk:{risk.coordination_risk.upper()}",
        "│",
        f"│  {risk.explanation}",
    ]
    if risk.blocking_reasons:
        lines.append("│  Blocking reasons:")
        for r in risk.blocking_reasons:
            lines.append(f"│    ! {r}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)
