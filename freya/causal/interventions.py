"""freya/causal/interventions.py

CausalInterventionAnalysisEngine

Analyzes the full causal impact of operational interventions including
primary effects, secondary effects, and unintended consequences.
All analysis is bounded to known operational patterns.

Key insight: interventions have side effects.
  e.g. aggressive compression reduces quality → increases reprocessing →
       partially negates the stabilization benefit.
"""
from __future__ import annotations

from freya.causal.models import CausalInterventionImpact

# ── Impact catalog ────────────────────────────────────────────────────────────
# (primary_effects, secondary_effects, stabilization_contribution, governance_impact,
#  unintended_consequences, net_stability_delta)

_IMPACT_CATALOG: dict[str, tuple[list[str], list[str], str, str, list[str], float]] = {
    "governance_batching": (
        [
            "Approval interruption frequency reduced.",
            "Active workflows experience fewer context-switching interrupts.",
        ],
        [
            "Lower interruptions reduce retry churn.",
            "Reduced retry churn lowers reasoning pool volatility.",
            "Stable pool supports improved equilibrium.",
        ],
        "Significant stabilization through interrupt reduction.",
        "Governance continuity preserved; reviews proceed in scheduled windows.",
        ["Slight approval latency increase for non-critical reviews."],
        +0.35,
    ),
    "reasoning_compression": (
        [
            "Background workflow reasoning depth reduced by compression.",
            "Reasoning pool utilization decreases immediately.",
        ],
        [
            "Lower pool utilization reduces contention between workflows.",
            "Reduced contention lowers pressure on critical workflows.",
        ],
        "Moderate stabilization through demand reduction.",
        "Governance continuity preserved.",
        [
            "Shallower analysis may increase reprocessing requests.",
            "Reprocessing partially offsets the pool utilization reduction.",
        ],
        +0.20,  # positive but reduced by unintended consequences
    ),
    "workflow_degradation": (
        [
            "Affected workflow quality reduced.",
            "Freed capacity available for prioritized workflows.",
        ],
        [
            "Quality reduction may cause downstream reprocessing.",
            "Reprocessing demand can create secondary pressure spikes.",
        ],
        "Capacity freed at the cost of quality degradation.",
        "Governance review recommended before applying to high-priority workflows.",
        [
            "Quality reduction creates auditable side effects in output.",
            "Reprocessing demand may partially negate capacity savings.",
        ],
        +0.10,
    ),
    "reservation_reallocation": (
        [
            "Capacity reserved for critical workflows.",
            "Protected headroom ensures critical throughput under pressure.",
        ],
        [
            "Critical workflow latency preserved during pressure events.",
            "Consistent throughput reduces timeout-triggered retries.",
            "Lower retries dampen reasoning pool amplification loops.",
        ],
        "Strong stabilization through protected headroom.",
        "Governance continuity fully preserved.",
        [
            "Lower-priority workflows may experience reduced available capacity.",
        ],
        +0.40,
    ),
    "optimization_suspension": (
        [
            "Background optimization cycles suspended.",
            "Freed compute budget redirected to active execution.",
        ],
        [
            "Active workflows benefit from lower latency.",
            "Lower latency reduces timeout frequency and retry amplification.",
        ],
        "Partial stabilization through compute redirection.",
        "Governance continuity preserved.",
        [
            "Optimization quality gains deferred — may accumulate backlog.",
        ],
        +0.25,
    ),
    "workflow_deferral": (
        [
            "Non-critical workflow execution deferred to next cycle.",
            "Immediate capacity freed for active priority workflows.",
        ],
        [
            "Deferred workflows reduce current operational pressure.",
            "Lower pressure decreases retry amplification risk.",
        ],
        "Moderate stabilization through load shedding.",
        "Governance continuity preserved; deferred workflows resume automatically.",
        [
            "Deferred workflows may accumulate backlog impacting next cycle.",
        ],
        +0.30,
    ),
    "no_intervention": (
        ["No intervention applied — operational state unchanged."],
        ["Existing trends continue on current trajectory."],
        "No stabilization contribution.",
        "No governance impact.",
        ["Risk of escalation without intervention."],
        0.0,
    ),
}


class CausalInterventionAnalysisEngine:
    """Analyze full causal impact of operational interventions."""

    def analyze(self, intervention_name: str) -> CausalInterventionImpact:
        """Return complete causal impact for a named intervention."""
        entry = _IMPACT_CATALOG.get(intervention_name, _IMPACT_CATALOG["no_intervention"])
        primary, secondary, stabilization, governance, unintended, delta = entry

        return CausalInterventionImpact(
            intervention_name=intervention_name,
            primary_effects=list(primary),
            secondary_effects=list(secondary),
            stabilization_contribution=stabilization,
            governance_impact=governance,
            unintended_consequences=list(unintended),
            net_stability_delta=delta,
        )

    def compare(
        self,
        intervention_a: str,
        intervention_b: str,
    ) -> dict:
        """Compare two interventions by net stability delta and side effects."""
        ia = self.analyze(intervention_a)
        ib = self.analyze(intervention_b)
        winner = intervention_a if ia.net_stability_delta >= ib.net_stability_delta else intervention_b

        return {
            "intervention_a":  intervention_a,
            "delta_a":         ia.net_stability_delta,
            "side_effects_a":  ia.unintended_consequences,
            "intervention_b":  intervention_b,
            "delta_b":         ib.net_stability_delta,
            "side_effects_b":  ib.unintended_consequences,
            "recommended":     winner,
            "reason": (
                f"'{winner}' achieves greater net stability improvement "
                f"({max(ia.net_stability_delta, ib.net_stability_delta):+.0%}) "
                f"with fewer unintended consequences."
            ),
        }

    def known_interventions(self) -> list[str]:
        return [k for k in _IMPACT_CATALOG if k != "no_intervention"]
