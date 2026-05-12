"""freya/sequencing/adaptation.py

Adaptive Intervention Engine.

Dynamically adjusts which interventions are applied based on phase,
pressure trend, and current intervention footprint. Avoids unnecessary
escalation and over-mitigation.

Design rules:
- Adapt progressively, never aggressively
- Defer escalation when stabilization is trending positive
- Recommend only the minimum necessary next action
"""
from __future__ import annotations

from freya.sequencing.models import AdaptiveInterventionDecision

# ---------------------------------------------------------------------------
# Adaptation rule catalog
# Each rule matches on phase, trend, required inclusions, and exclusions.
# Rule ordering matters: first match wins.
# ---------------------------------------------------------------------------
_RULES: list[dict] = [
    # --- retry_stabilization ---
    {
        "phase": "retry_stabilization",
        "trend": "improving",
        "includes": ["batching_applied"],
        "excludes": ["reasoning_compression"],
        "next_action": "Defer compression; continue monitoring batching effect",
        "reason": "Batching is producing stabilization. Compression at this stage would be premature and risk over-mitigation.",
        "equilibrium_effect": "Equilibrium preserved through minimal-footprint stabilization",
    },
    {
        "phase": "retry_stabilization",
        "trend": "stable",
        "includes": ["batching_applied"],
        "excludes": [],
        "next_action": "Maintain batching; monitor pressure for one additional cycle before escalating",
        "reason": "System is holding at current intervention level. Escalation should wait for trend confirmation.",
        "equilibrium_effect": "Low disruption; equilibrium trajectory holding",
    },
    {
        "phase": "retry_stabilization",
        "trend": "worsening",
        "includes": [],
        "excludes": [],
        "next_action": "Apply governance batching immediately; initiate smoothing if batching insufficient within one cycle",
        "reason": "Stabilization stalling under worsening pressure. Escalation to smoothing is warranted.",
        "equilibrium_effect": "Moderate disruption — necessary to prevent cascade escalation",
    },
    # --- governance_recovery ---
    {
        "phase": "governance_recovery",
        "trend": "improving",
        "includes": ["batching_applied"],
        "excludes": [],
        "next_action": "Continue batch processing; evaluate readiness to transition to contention_reduction phase",
        "reason": "Governance queue is clearing. Contention reduction may become the critical next phase.",
        "equilibrium_effect": "Governance pressure reducing; equilibrium trajectory positive",
    },
    {
        "phase": "governance_recovery",
        "trend": "stable",
        "includes": [],
        "excludes": [],
        "next_action": "Maintain current batching cadence; defer phase transition until queue visibly reducing",
        "reason": "Governance queue stabilizing but not yet clearing. Premature phase transition risks rebound.",
        "equilibrium_effect": "Equilibrium neutral; governance recovery on track but not complete",
    },
    {
        "phase": "governance_recovery",
        "trend": "worsening",
        "includes": [],
        "excludes": [],
        "next_action": "Increase batching frequency; add smoothing to reduce concurrent governance requests",
        "reason": "Governance congestion deepening. Combined batching and smoothing required to stop amplification.",
        "equilibrium_effect": "Short-term disruption to governance throughput; necessary for queue recovery",
    },
    # --- contention_reduction ---
    {
        "phase": "contention_reduction",
        "trend": "improving",
        "includes": ["smoothing_applied"],
        "excludes": ["reservation_applied"],
        "next_action": "Defer reservation; smoothing is providing sufficient contention relief",
        "reason": "Smoothing is reducing contention without reservation overhead. Over-committing resources would be wasteful.",
        "equilibrium_effect": "Equilibrium improving; reservation deferral avoids over-mitigation",
    },
    {
        "phase": "contention_reduction",
        "trend": "stable",
        "includes": [],
        "excludes": [],
        "next_action": "Monitor contention; hold reservation unless pressure remains above 0.55 after next cycle",
        "reason": "Contention stabilizing. Conditional reservation threshold set to avoid premature resource commitment.",
        "equilibrium_effect": "Equilibrium neutral; conditional escalation threshold in place",
    },
    {
        "phase": "contention_reduction",
        "trend": "worsening",
        "includes": [],
        "excludes": ["reservation_applied"],
        "next_action": "Apply targeted capacity reservation for critical workflows immediately",
        "reason": "Contention worsening despite current interventions. Reservation needed to protect critical throughput.",
        "equilibrium_effect": "Temporary resource rebalancing; stabilizes critical workflow pressure under contention",
    },
    # --- restoration ---
    {
        "phase": "restoration",
        "trend": "improving",
        "includes": [],
        "excludes": [],
        "next_action": "Begin gradual optimization restoration; taper batching at 20% increments per cycle",
        "reason": "System stable and improving. Conservative pacing ensures restoration does not trigger rebound.",
        "equilibrium_effect": "Progressive restoration; equilibrium maintained through incremental approach",
    },
    {
        "phase": "restoration",
        "trend": "stable",
        "includes": [],
        "excludes": [],
        "next_action": "Pause restoration increments; confirm stability for one additional cycle before continuing",
        "reason": "Stable but not yet improving. Conservative pause avoids premature optimization restoration.",
        "equilibrium_effect": "Equilibrium held; restoration paused to prevent rebound destabilization",
    },
    {
        "phase": "restoration",
        "trend": "worsening",
        "includes": [],
        "excludes": [],
        "next_action": "Suspend restoration; reactivate contention_reduction phase if pressure exceeds 0.50",
        "reason": "Unexpected worsening during restoration. Rollback to contention management prevents destabilization.",
        "equilibrium_effect": "Restoration suspended — equilibrium safeguard triggered",
    },
]

# Default fallback decision.
_DEFAULT_RULE: dict = {
    "next_action": "Maintain current intervention footprint; await trend clarification",
    "reason": "No specific adaptation rule matched the current operational context.",
    "equilibrium_effect": "Equilibrium monitoring active; no change recommended",
}


class AdaptiveInterventionEngine:
    """Selects the minimum necessary next intervention action given operational context."""

    def recommend(
        self,
        current_phase: str,
        current_pressure: float,
        active_interventions: list[str],
        pressure_trend: str,
    ) -> AdaptiveInterventionDecision:
        """Return an adaptive intervention decision for the current context.

        Args:
            current_phase: Name of the active operational phase.
            current_pressure: Operational pressure in [0.0, 1.0].
            active_interventions: List of currently applied interventions.
            pressure_trend: One of 'improving', 'stable', 'worsening'.
        """
        intervention_set = set(active_interventions)

        for rule in _RULES:
            if rule["phase"] != current_phase:
                continue
            if rule["trend"] != pressure_trend:
                continue
            if not all(inc in intervention_set for inc in rule["includes"]):
                continue
            if any(exc in intervention_set for exc in rule["excludes"]):
                continue

            return AdaptiveInterventionDecision(
                current_phase=current_phase,
                recommended_next_action=rule["next_action"],
                adaptation_reason=rule["reason"],
                equilibrium_effect=rule["equilibrium_effect"],
            )

        # No rule matched — use default.
        return AdaptiveInterventionDecision(
            current_phase=current_phase,
            recommended_next_action=_DEFAULT_RULE["next_action"],
            adaptation_reason=_DEFAULT_RULE["reason"],
            equilibrium_effect=_DEFAULT_RULE["equilibrium_effect"],
        )

    def should_escalate(
        self,
        current_pressure: float,
        pressure_trend: str,
        current_phase: str,
    ) -> bool:
        """Return True only when escalation is warranted by pressure + trend."""
        if pressure_trend == "worsening" and current_pressure > 0.65:
            return True
        if pressure_trend == "worsening" and current_phase == "restoration":
            return True
        return False
