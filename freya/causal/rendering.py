"""freya/causal/rendering.py

Human-readable rendering for the Causal Operational Reasoning layer.
Style: causally intelligent, operationally strategic, executive-friendly.
No graph-theory dumps. No AI chain-of-thought.
"""
from __future__ import annotations

from freya.causal.models import (
    CausalInterventionImpact,
    CausalPropagationChain,
    DestabilizationCascade,
    StabilizationPropagation,
)


def render_causal_chain(chain: CausalPropagationChain) -> str:
    """Render a propagation chain as an operational causal narrative."""
    strength_labels = {
        "cascading": "CASCADING — high amplification risk",
        "amplified": "Amplifying — secondary effects growing",
        "neutral":   "Neutral — limited secondary propagation",
        "dampened":  "Dampened — stabilization taking effect",
    }
    stabilization_labels = {
        "none": "None — risk remains",
        "partial": "Partial — monitoring required",
        "significant": "Significant — equilibrium improving",
        "strong": "Strong — equilibrium reinforced",
        "complete": "Complete — full stabilization",
    }

    lines = [
        "┌─ Operational Causal Analysis ──────────────────────────────────────┐",
        f"│  Chain ID:      {chain.chain_id}",
        f"│  Root event:    {chain.root_event.replace('_', ' ').title()}",
        f"│  Propagation:   {strength_labels.get(chain.propagation_strength, chain.propagation_strength)}",
        f"│  Confidence:    {chain.confidence_score:.0%}",
        "│",
        "│  Effect Chain:",
    ]
    for i, step in enumerate(chain.propagation_steps, start=1):
        lines.append(f"│    {i}. {step}")
    lines.append("│")
    lines.append(f"│  Projected Outcome:  {chain.projected_outcome}")
    lines.append(f"│  Stabilization:      {stabilization_labels.get(chain.stabilization_effect, chain.stabilization_effect)}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_cascade_analysis(cascade: DestabilizationCascade) -> str:
    """Render a destabilization cascade as an executive coordination alert."""
    risk_labels = {
        "none":     "None",
        "low":      "Low",
        "moderate": "Moderate — monitoring recommended",
        "high":     "High — proactive mitigation warranted",
        "imminent": "IMMINENT — immediate response required",
    }
    lines = [
        "┌─ Destabilization Cascade Analysis ─────────────────────────────────┐",
        f"│  Cascade ID:      {cascade.cascade_id}",
        f"│  Trigger:         {cascade.trigger_event.replace('_', ' + ')}",
        f"│  Equilibrium risk: {risk_labels.get(cascade.equilibrium_risk, cascade.equilibrium_risk)}",
        f"│  Amplifying:      {'Yes — feedback loop detected' if cascade.is_amplifying else 'No'}",
        f"│  Cascade depth:   {cascade.cascade_depth} hops",
        "│",
        "│  Projected Effects:",
    ]
    for effect in cascade.projected_cascade_effects:
        lines.append(f"│    • {effect}")
    lines.append("│")
    lines.append("│  Mitigation Recommendations:")
    for rec in cascade.mitigation_recommendations:
        lines.append(f"│    → {rec}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_intervention_causality(impact: CausalInterventionImpact) -> str:
    """Render a full causal intervention impact analysis."""
    sign = "+" if impact.net_stability_delta >= 0 else ""
    lines = [
        "┌─ Intervention Causal Impact ───────────────────────────────────────┐",
        f"│  Intervention:      {impact.intervention_name.replace('_', ' ').title()}",
        f"│  Net stability:     {sign}{impact.net_stability_delta:.0%}",
        "│",
        "│  Primary Effects:",
    ]
    for e in impact.primary_effects:
        lines.append(f"│    • {e}")
    lines.append("│")
    lines.append("│  Secondary Effects:")
    for e in impact.secondary_effects:
        lines.append(f"│    → {e}")
    if impact.unintended_consequences:
        lines.append("│")
        lines.append("│  Unintended Consequences:")
        for c in impact.unintended_consequences:
            lines.append(f"│    ! {c}")
    lines.append("│")
    lines.append(f"│  Stabilization: {impact.stabilization_contribution}")
    lines.append(f"│  Governance:    {impact.governance_impact}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_stabilization_propagation(prop: StabilizationPropagation) -> str:
    """Render a stabilization propagation analysis."""
    effect_labels = {
        "none":        "None",
        "partial":     "Partial",
        "significant": "Significant",
        "strong":      "Strong",
        "complete":    "Complete",
    }
    lines = [
        "┌─ Stabilization Propagation ─────────────────────────────────────────┐",
        f"│  Intervention:  {prop.intervention_name.replace('_', ' ').title()}",
        f"│  Impact:        {effect_labels.get(prop.equilibrium_impact, prop.equilibrium_impact)}",
        "│",
        f"│  Primary: {prop.primary_stabilization}",
        "│",
        "│  Propagated Benefits:",
    ]
    for b in prop.propagated_benefits:
        lines.append(f"│    • {b}")
    lines.append("│")
    lines.append("│  Reinforcement Chain:")
    for i, step in enumerate(prop.reinforcement_chain, start=1):
        lines.append(f"│    {i}. {step}")
    lines.append("│")
    lines.append(f"│  Durability: {prop.durability_estimate}")
    lines.append("└─────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)
