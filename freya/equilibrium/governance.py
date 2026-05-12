"""freya/equilibrium/governance.py

Equilibrium Governance Layer.

Validates cross-zone recovery ordering, restricts destabilizing recovery
sequences, and enforces bounded equilibrium coordination.

Hard rules:
- Unsafe simultaneous recovery of multiple unstable zones is blocked
- Governance zone must stabilize before delegation restoration
- Critical zones always recover conservatively
- High-pressure zones with unclear trend require human review
"""
from __future__ import annotations

from freya.equilibrium.models import (
    MultiEquilibriumAssessment,
    OperationalEquilibriumZone,
    ZoneRecoveryPlan,
)

# Zones that must stabilize before dependent zones may begin restoration.
_PREREQUISITES: dict[str, list[str]] = {
    "delegation":    ["governance"],
    "optimization":  ["reasoning"],
    "coordination":  ["governance", "reasoning"],
}

# Maximum number of zones that may be restored simultaneously.
_MAX_SIMULTANEOUS_RESTORATIONS = 2

_UNSAFE_REBOUND_ACTIONS: frozenset[str] = frozenset(
    {
        "instant full restoration",
        "simultaneous zone restoration",
        "force restore all zones",
        "bypass zone prerequisites",
        "global recovery",
    }
)


class EquilibriumGovernanceEngine:
    """Validates zone recovery scheduling for safety and governance compliance."""

    def validate_recovery_order(
        self,
        recovery_order: list[str],
        zones: dict[str, OperationalEquilibriumZone],
    ) -> tuple[bool, list[str]]:
        """Validate that a proposed zone recovery ordering is safe.

        Args:
            recovery_order: Zone keys in proposed recovery sequence.
            zones: Current zone states.

        Returns (is_valid, violations).
        """
        violations: list[str] = []
        seen: set[str] = set()

        for zone_key in recovery_order:
            prereqs = _PREREQUISITES.get(zone_key, [])
            for prereq_key in prereqs:
                prereq_zone = zones.get(prereq_key)
                if prereq_zone is None:
                    continue
                # Prerequisite must be in a stabilized or restored state, or appear earlier in order.
                prereq_stable = prereq_zone.equilibrium_state in ("stabilized", "restored")
                prereq_earlier = prereq_key in seen
                if not prereq_stable and not prereq_earlier:
                    violations.append(
                        f"Zone '{zone_key}' recovery scheduled before prerequisite '{prereq_key}' "
                        f"is stabilized (current state: {prereq_zone.equilibrium_state})."
                    )
            seen.add(zone_key)

        # Check simultaneous restoration count.
        unstable_in_order = [
            k for k in recovery_order
            if k in zones and zones[k].equilibrium_state == "unstable"
        ]
        if len(unstable_in_order) > _MAX_SIMULTANEOUS_RESTORATIONS:
            violations.append(
                f"Recovery order includes {len(unstable_in_order)} unstable zones simultaneously. "
                f"Maximum safe simultaneous recovery is {_MAX_SIMULTANEOUS_RESTORATIONS}. "
                "Stagger recovery to avoid synchronized rebound."
            )

        return (len(violations) == 0, violations)

    def validate_recovery_plan(
        self, plan: ZoneRecoveryPlan
    ) -> tuple[bool, list[str]]:
        """Validate a zone recovery plan for unsafe actions.

        Returns (is_valid, violations).
        """
        violations: list[str] = []
        for action in plan.restoration_actions:
            action_lower = action.lower()
            for unsafe in _UNSAFE_REBOUND_ACTIONS:
                if unsafe in action_lower:
                    violations.append(
                        f"Recovery plan for '{plan.zone_name}' contains unsafe action: '{action[:60]}...'"
                    )

        if plan.rebound_risk == "high" and plan.pacing_strategy.lower().startswith("full"):
            violations.append(
                f"Recovery plan for '{plan.zone_name}' has high rebound risk "
                "but pacing strategy starts with 'full' — conservative pacing required."
            )

        return (len(violations) == 0, violations)

    def validate_assessment(
        self, assessment: MultiEquilibriumAssessment
    ) -> tuple[bool, list[str]]:
        """Validate a MultiEquilibriumAssessment for critical risk signals.

        Returns (is_valid, violations).
        """
        violations: list[str] = []
        if assessment.coordination_risk == "critical":
            violations.append(
                "Multi-equilibrium assessment shows CRITICAL coordination risk — "
                "human review required before any cross-zone recovery action."
            )
        if len(assessment.unstable_zones) >= 4:
            violations.append(
                f"{len(assessment.unstable_zones)} zones simultaneously unstable — "
                "system-wide stabilization emergency; escalate to human operator."
            )
        return (len(violations) == 0, violations)

    def review_required(
        self,
        zones: dict[str, OperationalEquilibriumZone],
        confidence: float,
    ) -> bool:
        """Return True when the current zone state warrants human review."""
        if confidence < 0.55:
            return True
        critical_count = sum(
            1 for z in zones.values() if z.pressure_level >= 0.75
        )
        if critical_count >= 2:
            return True
        return False
