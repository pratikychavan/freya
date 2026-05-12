"""freya/topology/sustainability.py

Long-Horizon Operational Sustainability Engine.

Reasons about future resilience across multiple operational cycles by
examining active topology patterns and current interventions. Identifies
compounding risk factors that are not visible in single-cycle analysis.
"""
from __future__ import annotations


# Maps intervention names to their long-horizon risk contributions.
_INTERVENTION_RISK_PROFILE: dict[str, dict] = {
    "batching": {
        "risk_label": "throughput_drag",
        "onset_cycles": 5,
        "description": (
            "Sustained governance batching beyond 5 cycles introduces latency "
            "accumulation, reducing effective approval throughput."
        ),
        "mitigation": "Taper batching at cycle 4; introduce priority review windows.",
    },
    "compression": {
        "risk_label": "operational_trust_degradation",
        "onset_cycles": 4,
        "description": (
            "Chronic reasoning compression degrades analysis depth, eroding "
            "operational trust in output quality over time."
        ),
        "mitigation": "Cap compression at 3 cycles; alternate with batching rotation.",
    },
    "smoothing": {
        "risk_label": "strategic_recovery_delay",
        "onset_cycles": 5,
        "description": (
            "Persistent smoothing masks underlying contention causes, delaying "
            "the structural interventions needed for full strategic recovery."
        ),
        "mitigation": (
            "Limit smoothing to a bridge role (≤ 4 cycles); escalate to root-cause "
            "interventions before cycle 5."
        ),
    },
    "reservation": {
        "risk_label": "capacity_lock-in",
        "onset_cycles": 8,
        "description": (
            "Long-running capacity reservations can create implicit lock-in, "
            "reducing operational flexibility for future workload shifts."
        ),
        "mitigation": "Review reservation scope at cycle 6; release non-critical reservations.",
    },
    "sequencing_lockout": {
        "risk_label": "coordination_brittleness",
        "onset_cycles": 6,
        "description": (
            "Sustained sequencing lockouts reduce coordination path diversity, "
            "increasing brittleness if a primary path fails."
        ),
        "mitigation": "Maintain at least one alternate coordination path in active state.",
    },
}


class LongHorizonOperationalSustainabilityEngine:
    """Assesses operational sustainability across a multi-cycle forward horizon."""

    def assess(
        self,
        active_topology_count: int,
        active_interventions: list[str],
        horizon_cycles: int = 5,
    ) -> dict:
        """Produce a sustainability assessment for the given forward horizon.

        Parameters
        ----------
        active_topology_count:
            Number of topology patterns currently active.
        active_interventions:
            List of active intervention identifiers (e.g. "batching", "compression").
        horizon_cycles:
            Forward cycle horizon for risk projection.

        Returns
        -------
        dict with keys:
            sustainability_state, resilience_outlook, future_risk_factors,
            recommended_rotation, cycle_horizon
        """
        future_risks: list[str] = []
        mitigations: list[str] = []

        for intervention in active_interventions:
            profile = _INTERVENTION_RISK_PROFILE.get(intervention)
            if profile and horizon_cycles >= profile["onset_cycles"]:
                future_risks.append(
                    f"{intervention.upper()} → {profile['risk_label']}: {profile['description']}"
                )
                mitigations.append(f"{intervention}: {profile['mitigation']}")

        # Compute sustainability state
        risk_count = len(future_risks)
        if risk_count == 0 and active_topology_count <= 2:
            sustainability_state = "sustainable"
            resilience_outlook = "resilient"
        elif risk_count <= 1 or (risk_count == 0 and active_topology_count > 2):
            sustainability_state = "watchlist"
            resilience_outlook = "at_risk"
        elif risk_count == 2:
            sustainability_state = "degrading"
            resilience_outlook = "degrading"
        else:
            sustainability_state = "critical"
            resilience_outlook = "critical"

        recommended_rotation = (
            mitigations
            if mitigations
            else ["No intervention rotation required within the current horizon."]
        )

        return {
            "sustainability_state": sustainability_state,
            "resilience_outlook": resilience_outlook,
            "future_risk_factors": future_risks if future_risks else ["None projected within horizon."],
            "recommended_rotation": recommended_rotation,
            "cycle_horizon": horizon_cycles,
        }
