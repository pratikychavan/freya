"""freya/equilibrium/recovery.py

Asynchronous Recovery Coordination Engine.

Coordinates zone-specific recovery pacing to avoid synchronized rebound
instability. Each zone recovers independently at a rate anchored to its
own pressure trajectory — NOT global system state.

Recovery order preference:
  1. Governance   (reduces retry amplification cascade)
  2. Coordination (unblocks workflow throughput)
  3. Reasoning    (restores analytical quality)
  4. Optimization (restores depth — comes last)
  5. Delegation   (deferred until governance stable)
  6. Recovery     (meta — follows other zones)
"""
from __future__ import annotations

from freya.equilibrium.models import OperationalEquilibriumZone, ZoneRecoveryPlan

# ---------------------------------------------------------------------------
# Zone-specific recovery plan templates, keyed by (zone_key, pressure_band)
# pressure_band: "high" (>=0.60), "mid" (0.40–0.59), "low" (<0.40)
# ---------------------------------------------------------------------------
_PLANS: dict[str, dict[str, dict]] = {
    "governance": {
        "high": {
            "restoration_actions": [
                "Apply governance batching to drain approval queue backlog.",
                "Suspend non-critical approval pathways until queue normalizes.",
                "Monitor retry rate for signs of batching effectiveness each cycle.",
            ],
            "pacing_strategy": "Aggressive batching — queue relief is the priority.",
            "projected_recovery_window": "2–3 cycles",
            "rebound_risk": "moderate",
        },
        "mid": {
            "restoration_actions": [
                "Reduce batching frequency by 25% — queue stabilizing.",
                "Re-enable priority approval pathway for critical workflows.",
                "Continue monitoring queue depth before full batching removal.",
            ],
            "pacing_strategy": "Conservative tapering — preserve queue gains.",
            "projected_recovery_window": "1–2 cycles",
            "rebound_risk": "low",
        },
        "low": {
            "restoration_actions": [
                "Remove governance batching — queue at normal capacity.",
                "Restore standard approval cadence across all workflows.",
                "Log governance zone stabilization for audit record.",
            ],
            "pacing_strategy": "Full restoration — governance zone recovered.",
            "projected_recovery_window": "Complete",
            "rebound_risk": "low",
        },
    },
    "reasoning": {
        "high": {
            "restoration_actions": [
                "Apply reasoning depth compression to reduce pool utilization.",
                "Defer non-critical reasoning tasks until saturation clears.",
                "Monitor pool utilization trend before relaxing compression.",
            ],
            "pacing_strategy": "Compression-led relief — depth sacrificed temporarily.",
            "projected_recovery_window": "3–4 cycles",
            "rebound_risk": "high",
        },
        "mid": {
            "restoration_actions": [
                "Restore reasoning depth to 60% of baseline — partial only.",
                "Monitor contention for rebound before each increment.",
                "Defer full restoration until governance zone confirms stable.",
            ],
            "pacing_strategy": "Partial restoration — 20% depth increments per cycle.",
            "projected_recovery_window": "2 cycles",
            "rebound_risk": "moderate",
        },
        "low": {
            "restoration_actions": [
                "Restore reasoning depth to full baseline.",
                "Remove compression configuration.",
                "Confirm no pool contention rebound over 1 cycle.",
            ],
            "pacing_strategy": "Full restoration — reasoning zone recovered.",
            "projected_recovery_window": "Complete",
            "rebound_risk": "low",
        },
    },
    "optimization": {
        "high": {
            "restoration_actions": [
                "Suspend optimization activity — capacity reallocated to governance/reasoning.",
                "Monitor reasoning and governance zone pressure before restoring optimization.",
                "Log optimization suspension for recovery audit.",
            ],
            "pacing_strategy": "Full suspension — optimization deferred.",
            "projected_recovery_window": "Deferred until reasoning zone recovers",
            "rebound_risk": "low",
        },
        "mid": {
            "restoration_actions": [
                "Restore optimization to 40% capacity — cautious re-entry.",
                "Activate smoothing to taper background optimization load.",
                "Confirm no reasoning pressure increase before adding capacity.",
            ],
            "pacing_strategy": "Stepped restoration — 20% increments, reasoning-gated.",
            "projected_recovery_window": "2–3 cycles",
            "rebound_risk": "moderate",
        },
        "low": {
            "restoration_actions": [
                "Restore full optimization capacity.",
                "Remove smoothing taper configuration.",
                "Confirm reasoning zone remains stable under full optimization load.",
            ],
            "pacing_strategy": "Full restoration — optimization zone recovered.",
            "projected_recovery_window": "Complete",
            "rebound_risk": "low",
        },
    },
    "delegation": {
        "high": {
            "restoration_actions": [
                "Suspend new delegation contract activations.",
                "Route delegation requests through governance review gate.",
                "Defer delegation restoration until governance zone stabilized.",
            ],
            "pacing_strategy": "Suspension — delegation deferred until governance stable.",
            "projected_recovery_window": "Deferred — governance prerequisite",
            "rebound_risk": "high",
        },
        "mid": {
            "restoration_actions": [
                "Restore low-priority delegation pathways only.",
                "Gate critical delegation restoration on governance zone confirmation.",
                "Monitor governance load impact of each delegation increment.",
            ],
            "pacing_strategy": "Priority-gated — low-risk pathways first.",
            "projected_recovery_window": "2 cycles after governance confirms stable",
            "rebound_risk": "moderate",
        },
        "low": {
            "restoration_actions": [
                "Restore full delegation capacity.",
                "Remove governance delegation gate.",
                "Log delegation zone restoration.",
            ],
            "pacing_strategy": "Full restoration — delegation zone recovered.",
            "projected_recovery_window": "Complete",
            "rebound_risk": "low",
        },
    },
    "coordination": {
        "high": {
            "restoration_actions": [
                "Reduce concurrent coordination load by deferring low-priority workflows.",
                "Apply scheduling smoothing across active coordination pathways.",
                "Monitor reasoning and governance zones — coordination recovery depends on both.",
            ],
            "pacing_strategy": "Deferred load — priority contention relief.",
            "projected_recovery_window": "3 cycles",
            "rebound_risk": "moderate",
        },
        "mid": {
            "restoration_actions": [
                "Re-enable deferred workflows progressively.",
                "Remove scheduling smoothing once throughput normalizes.",
                "Confirm reasoning zone pressure remains stable.",
            ],
            "pacing_strategy": "Progressive re-enablement — throughput-gated.",
            "projected_recovery_window": "1–2 cycles",
            "rebound_risk": "low",
        },
        "low": {
            "restoration_actions": [
                "Restore full coordination scheduling.",
                "Log coordination zone stabilization.",
            ],
            "pacing_strategy": "Full restoration — coordination zone recovered.",
            "projected_recovery_window": "Complete",
            "rebound_risk": "low",
        },
    },
    "recovery": {
        "high": {
            "restoration_actions": [
                "Prioritize active incident recovery over restoration activity.",
                "Defer optimization and delegation recovery until primary incidents resolved.",
                "Maintain recovery audit logging at elevated cadence.",
            ],
            "pacing_strategy": "Incident-first — recovery zone in active triage.",
            "projected_recovery_window": "Dependent on incident resolution",
            "rebound_risk": "high",
        },
        "mid": {
            "restoration_actions": [
                "Begin staged restoration of non-critical recovery pathways.",
                "Confirm incident backlog reducing before scaling recovery capacity.",
            ],
            "pacing_strategy": "Phased recovery resumption.",
            "projected_recovery_window": "2 cycles",
            "rebound_risk": "moderate",
        },
        "low": {
            "restoration_actions": [
                "Restore full recovery coordination capacity.",
                "Close active incident recovery audit record.",
            ],
            "pacing_strategy": "Full restoration — recovery zone normalized.",
            "projected_recovery_window": "Complete",
            "rebound_risk": "low",
        },
    },
}


def _pressure_band(pressure: float) -> str:
    if pressure >= 0.60:
        return "high"
    if pressure >= 0.40:
        return "mid"
    return "low"


class AsynchronousRecoveryCoordinationEngine:
    """Returns zone-specific, pressure-anchored recovery plans."""

    def plan_for_zone(
        self,
        zone_key: str,
        zone: OperationalEquilibriumZone,
    ) -> ZoneRecoveryPlan:
        """Return a ZoneRecoveryPlan for a single zone.

        Args:
            zone_key: The lowercase zone identifier key.
            zone: The current state of the zone.
        """
        band = _pressure_band(zone.pressure_level)
        zone_plans = _PLANS.get(zone_key, _PLANS["coordination"])
        template = zone_plans.get(band, zone_plans["low"])
        return ZoneRecoveryPlan(
            zone_name=zone.zone_name,
            restoration_actions=list(template["restoration_actions"]),
            pacing_strategy=template["pacing_strategy"],
            projected_recovery_window=template["projected_recovery_window"],
            rebound_risk=template["rebound_risk"],
        )

    def plan_all_zones(
        self,
        zones: dict[str, OperationalEquilibriumZone],
    ) -> dict[str, ZoneRecoveryPlan]:
        """Return a recovery plan for every zone.

        Args:
            zones: Mapping of zone_key → OperationalEquilibriumZone.
        """
        return {
            key: self.plan_for_zone(key, zone)
            for key, zone in zones.items()
        }

    def recovery_order(
        self, zones: dict[str, OperationalEquilibriumZone]
    ) -> list[str]:
        """Return zone keys sorted by recommended recovery priority.

        Zones with higher pressure get earlier recovery priority.
        Governance is always prioritized first (offset applied).
        """
        priority_offsets = {
            "governance": -0.20,
            "coordination": -0.10,
            "reasoning": 0.0,
            "optimization": 0.05,
            "delegation": 0.10,
            "recovery": 0.05,
        }
        return sorted(
            zones.keys(),
            key=lambda k: -(zones[k].pressure_level + priority_offsets.get(k, 0.0)),
        )
