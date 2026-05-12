"""freya/causal/stability.py

CausalStabilityEngine

Reasons about how stabilization effects propagate through the
operational graph — durability, reinforcement chains, and
equilibrium persistence. All reasoning is operationally bounded.
"""
from __future__ import annotations

from freya.causal.models import (
    CausalPropagationChain,
    StabilizationPropagation,
    StabilizationEffect,
)

# ── Stabilization propagation templates ───────────────────────────────────────

_STABILIZATION_TEMPLATES: dict[str, tuple[str, list[str], list[str], str, StabilizationEffect]] = {
    "batching_applied": (
        "Governance review interruptions reduced by batching.",
        [
            "Fewer interruptions lower retry frequency across active workflows.",
            "Lower retry frequency reduces reasoning pool volatility.",
            "Stable pool utilization decreases degradation probability.",
        ],
        [
            "Initial batching → reduced interruptions",
            "Reduced interruptions → lower retry churn",
            "Lower retry churn → stable reasoning pool",
            "Stable pool → reduced degradation pressure",
        ],
        "Durable while backlog remains below batch threshold.",
        "strong",
    ),
    "smoothing_applied": (
        "Background reasoning gradually tapered.",
        [
            "Progressive compression prevents sudden contention spikes.",
            "Smoother load curve reduces pool exhaustion risk.",
            "Lower exhaustion risk decreases the probability of cascading degradation.",
        ],
        [
            "Gradient compression → smoother demand curve",
            "Smoother demand → lower peak contention",
            "Lower peak contention → reduced degradation frequency",
        ],
        "Persists until pressure drops and smoothing phase steps down.",
        "significant",
    ),
    "reservation_applied": (
        "Critical workflow capacity protected via proactive reservation.",
        [
            "Protected headroom preserves critical-workflow throughput under pressure.",
            "Consistent throughput reduces timeout-driven retry amplification.",
            "Lower retry amplification stabilizes reasoning pool utilization.",
        ],
        [
            "Reservation → protected headroom",
            "Protected headroom → consistent throughput",
            "Consistent throughput → lower retries",
            "Lower retries → stable reasoning pool",
        ],
        "Persists until reservation expiry condition is met.",
        "significant",
    ),
    "optimization_suspended": (
        "Background optimization cycles suspended.",
        [
            "Freed optimization budget redirects to active workflow execution.",
            "Active workflows experience lower execution latency.",
            "Lower latency reduces timeout frequency and associated retry churn.",
        ],
        [
            "Suspension → freed compute",
            "Freed compute → lower execution latency",
            "Lower latency → fewer timeouts",
            "Fewer timeouts → lower retry rate",
        ],
        "Active while optimization suspension contract holds.",
        "partial",
    ),
    "no_intervention": (
        "No stabilization intervention applied.",
        ["Operational state continues on current trajectory."],
        ["Current trajectory maintained without reinforcement."],
        "No reinforcement — state may deteriorate.",
        "none",
    ),
}


def _assess_durability(effect: StabilizationEffect, pressure: float) -> str:
    if effect in ("complete", "strong") and pressure <= 0.60:
        return "High durability — reinforcement is self-sustaining at current pressure."
    if effect in ("significant",) and pressure <= 0.75:
        return "Moderate durability — reinforcement holds while pressure remains below 0.75."
    if effect in ("partial",):
        return "Partial durability — reinforcement degrades if pressure rises above 0.70."
    return "Low durability — additional intervention may be required."


class CausalStabilityEngine:
    """Reason about how stabilization propagates and persists."""

    def analyze(
        self,
        intervention_name: str,
        current_pressure: float = 0.60,
    ) -> StabilizationPropagation:
        """Return a stabilization propagation analysis for an intervention."""
        template = _STABILIZATION_TEMPLATES.get(
            intervention_name, _STABILIZATION_TEMPLATES["no_intervention"]
        )
        primary, benefits, chain, durability_template, effect = template

        durability = _assess_durability(effect, current_pressure)

        return StabilizationPropagation(
            intervention_name=intervention_name,
            primary_stabilization=primary,
            propagated_benefits=list(benefits),
            reinforcement_chain=list(chain),
            durability_estimate=durability,
            equilibrium_impact=effect,
        )

    def combined_stability(
        self,
        interventions: list[str],
        current_pressure: float = 0.60,
    ) -> StabilizationEffect:
        """Estimate the combined stabilization effect of multiple interventions."""
        effect_scores = {
            "none": 0, "partial": 1, "significant": 2, "strong": 3, "complete": 4
        }
        templates = {
            k: v for k, v in _STABILIZATION_TEMPLATES.items() if k in interventions
        }
        if not templates:
            return "none"

        max_score = max(effect_scores.get(t[4], 0) for t in templates.values())
        # Combined effect can exceed individual effects (reinforcement)
        bonus = min(len(templates) - 1, 1)
        combined = min(max_score + bonus, 4)
        reverse_map = {v: k for k, v in effect_scores.items()}
        return reverse_map.get(combined, "partial")  # type: ignore[return-value]

    def known_interventions(self) -> list[str]:
        return [k for k in _STABILIZATION_TEMPLATES if k != "no_intervention"]
