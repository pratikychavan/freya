"""freya/equilibrium/balancing.py

Operational Equilibrium Balancing Engine.

Redistributes stabilization effort across zones to prevent localized
overload and preserve organizational continuity. Zones are balanced
strategically — NOT restored globally.

Balancing rules:
- Do not accelerate optimization restoration while reasoning unstable
- Do not restore delegation while governance unstable
- Taper smoothing asymmetrically based on per-zone pressure trends
- Reduce optimization pace if it would push reasoning above threshold
"""
from __future__ import annotations

from freya.equilibrium.models import OperationalEquilibriumZone


# ---------------------------------------------------------------------------
# Balancing constraint rules
# Each rule defines a condition and a recommended balancing action.
# ---------------------------------------------------------------------------
_BALANCING_RULES: list[dict] = [
    {
        "name": "defer_optimization_during_reasoning_instability",
        "trigger_zone": "reasoning",
        "trigger_threshold": 0.60,
        "affected_zone": "optimization",
        "recommendation": (
            "Defer optimization restoration — reasoning zone pressure {reasoning_pressure:.0%} "
            "exceeds 0.60. Optimization restoration would compete for shared capacity."
        ),
        "balancing_action": "Pause optimization restoration until reasoning pressure drops below 0.55.",
    },
    {
        "name": "defer_delegation_during_governance_instability",
        "trigger_zone": "governance",
        "trigger_threshold": 0.55,
        "affected_zone": "delegation",
        "recommendation": (
            "Defer delegation recovery — governance zone pressure {governance_pressure:.0%} "
            "requires stabilization first. Delegation restoration increases governance load."
        ),
        "balancing_action": "Gate delegation recovery on governance pressure falling below 0.45.",
    },
    {
        "name": "taper_smoothing_when_coordination_stabilizes",
        "trigger_zone": "coordination",
        "trigger_threshold": 0.40,   # triggered when coordination drops BELOW threshold
        "trigger_direction": "below",
        "affected_zone": "reasoning",
        "recommendation": (
            "Coordination zone pressure {coordination_pressure:.0%} below 0.40 — "
            "smoothing intensity can be reduced without risking coordination rebound."
        ),
        "balancing_action": "Reduce smoothing by 20% to release reasoning capacity conservatively.",
    },
    {
        "name": "prioritize_governance_over_optimization",
        "trigger_zone": "governance",
        "trigger_threshold": 0.65,
        "affected_zone": "optimization",
        "recommendation": (
            "Governance pressure {governance_pressure:.0%} is critical. "
            "Optimization resources should be reallocated to governance stabilization."
        ),
        "balancing_action": "Suspend optimization; redirect capacity to governance batching.",
    },
    {
        "name": "allow_staggered_restoration_when_stable",
        "trigger_zone": "governance",
        "trigger_threshold": 0.35,   # triggered when governance drops BELOW threshold
        "trigger_direction": "below",
        "affected_zone": "coordination",
        "recommendation": (
            "Governance zone stabilized at {governance_pressure:.0%}. "
            "Coordination zone restoration can begin at conservative pacing."
        ),
        "balancing_action": "Begin coordination restoration at 20% capacity increments.",
    },
]


def _rule_triggered(
    rule: dict, zones: dict[str, OperationalEquilibriumZone]
) -> bool:
    trigger_key = rule["trigger_zone"]
    if trigger_key not in zones:
        return False
    pressure = zones[trigger_key].pressure_level
    direction = rule.get("trigger_direction", "above")
    threshold = rule["trigger_threshold"]
    if direction == "above":
        return pressure >= threshold
    return pressure < threshold


def _format_recommendation(template: str, zones: dict[str, OperationalEquilibriumZone]) -> str:
    ctx = {f"{k}_pressure": v.pressure_level for k, v in zones.items()}
    try:
        return template.format(**ctx)
    except KeyError:
        return template


class OperationalEquilibriumBalancingEngine:
    """Determines per-zone balancing adjustments to maintain coordinated stability."""

    def balance(
        self,
        zones: dict[str, OperationalEquilibriumZone],
    ) -> list[dict]:
        """Return a list of balancing recommendations for the current zone state.

        Each entry has:
            rule_name (str)
            affected_zone (str)
            recommendation (str)
            balancing_action (str)
        """
        recommendations: list[dict] = []
        for rule in _BALANCING_RULES:
            if not _rule_triggered(rule, zones):
                continue
            affected_key = rule["affected_zone"]
            affected_name = (
                zones[affected_key].zone_name
                if affected_key in zones
                else affected_key.title() + " Zone"
            )
            recommendations.append(
                {
                    "rule_name": rule["name"],
                    "affected_zone": affected_name,
                    "recommendation": _format_recommendation(rule["recommendation"], zones),
                    "balancing_action": rule["balancing_action"],
                }
            )
        return recommendations

    def should_pause_zone_restoration(
        self,
        zone_key: str,
        zones: dict[str, OperationalEquilibriumZone],
    ) -> tuple[bool, str]:
        """Return (should_pause, reason) for a zone's restoration attempt.

        Used by the engine to gate individual zone recovery actions.
        """
        # Hardcoded governance checks for the two most critical dependencies.
        if zone_key == "delegation":
            gov = zones.get("governance")
            if gov and gov.pressure_level >= 0.55:
                return (
                    True,
                    f"Delegation restoration paused — governance pressure "
                    f"{gov.pressure_level:.0%} must fall below 0.45 first.",
                )
        if zone_key == "optimization":
            rsn = zones.get("reasoning")
            if rsn and rsn.pressure_level >= 0.60:
                return (
                    True,
                    f"Optimization restoration paused — reasoning pressure "
                    f"{rsn.pressure_level:.0%} must fall below 0.55 first.",
                )
        return (False, "No balancing constraint applies.")
