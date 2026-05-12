"""freya/equilibrium/engine.py

Multi-Equilibrium Operational Engine — central coordinator.

Orchestrates: zone management → propagation → recovery → balancing → governance.
All coordination is bounded, explainable, and governance-approved.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from freya.equilibrium.balancing import OperationalEquilibriumBalancingEngine
from freya.equilibrium.governance import EquilibriumGovernanceEngine
from freya.equilibrium.models import (
    MultiEquilibriumAssessment,
    OperationalEquilibriumZone,
    ZonePropagationEffect,
    ZoneRecoveryPlan,
)
from freya.equilibrium.propagation import CrossZonePropagationEngine
from freya.equilibrium.recovery import AsynchronousRecoveryCoordinationEngine
from freya.equilibrium.zones import OperationalZoneManagementEngine


def _global_stability(
    unstable: list[str], recovering: list[str], total: int
) -> str:
    n_unstable = len(unstable)
    n_recovering = len(recovering)
    n_stable = total - n_unstable - n_recovering
    if n_unstable >= 4:
        return "critical"
    if n_unstable >= 2:
        return "unstable"
    if n_unstable == 1 and n_recovering >= 2:
        return "mixed"
    if n_unstable == 0 and n_recovering > 0:
        return "stabilizing"
    if n_stable == total:
        return "stable"
    return "mixed"


def _coordination_risk(
    unstable: list[str], effects: list[ZonePropagationEffect]
) -> str:
    high_effects = sum(1 for e in effects if e.severity == "high")
    if len(unstable) >= 3 or high_effects >= 3:
        return "critical"
    if len(unstable) >= 2 or high_effects >= 2:
        return "high"
    if len(unstable) == 1 or high_effects >= 1:
        return "moderate"
    return "low"


@dataclass
class MultiEquilibriumReport:
    """Complete output from a multi-equilibrium operational analysis."""

    pressure_map: dict[str, float]
    confidence: float

    zones: dict[str, OperationalEquilibriumZone] = field(default_factory=dict)
    propagation_effects: list[ZonePropagationEffect] = field(default_factory=list)
    recovery_plans: dict[str, ZoneRecoveryPlan] = field(default_factory=dict)
    recovery_order: list[str] = field(default_factory=list)
    balancing_recommendations: list[dict] = field(default_factory=list)
    assessment: MultiEquilibriumAssessment | None = None
    governance_violations: list[str] = field(default_factory=list)
    review_required: bool = False


class MultiEquilibriumOperationalEngine:
    """Coordinates parallel equilibrium zone management with staggered recovery."""

    def __init__(self) -> None:
        self._zones = OperationalZoneManagementEngine()
        self._propagation = CrossZonePropagationEngine()
        self._recovery = AsynchronousRecoveryCoordinationEngine()
        self._balancing = OperationalEquilibriumBalancingEngine()
        self._governance = EquilibriumGovernanceEngine()

    def analyze(
        self,
        pressure_map: dict[str, float],
        confidence: float = 0.70,
    ) -> MultiEquilibriumReport:
        """Run a full multi-equilibrium operational analysis.

        Args:
            pressure_map: Per-zone pressure overrides, e.g.
                          {"governance": 0.72, "reasoning": 0.80, "optimization": 0.45}.
                          Zones not mentioned use their defaults.
            confidence: Operational confidence level in [0.0, 1.0].

        Returns:
            MultiEquilibriumReport with all sub-analyses populated.
        """
        report = MultiEquilibriumReport(
            pressure_map=dict(pressure_map),
            confidence=confidence,
        )

        # 1. Build all zones.
        report.zones = self._zones.build_all_zones(pressure_map)

        # 2. Detect cross-zone propagation effects.
        report.propagation_effects = self._propagation.detect_effects(report.zones)

        # 3. Recovery plans (all zones).
        report.recovery_plans = self._recovery.plan_all_zones(report.zones)

        # 4. Recommended recovery order.
        report.recovery_order = self._recovery.recovery_order(report.zones)

        # Governance: validate recovery order.
        valid_order, order_violations = self._governance.validate_recovery_order(
            report.recovery_order, report.zones
        )
        report.governance_violations.extend(order_violations)

        # Governance: validate each recovery plan.
        for zone_key, plan in report.recovery_plans.items():
            _, plan_violations = self._governance.validate_recovery_plan(plan)
            report.governance_violations.extend(plan_violations)

        # 5. Balancing recommendations.
        report.balancing_recommendations = self._balancing.balance(report.zones)

        # 6. Classify zones for assessment.
        unstable, recovering, stabilized = self._zones.classify_zones(report.zones)

        # 7. Build multi-equilibrium assessment.
        global_stab = _global_stability(unstable, recovering, len(report.zones))
        coord_risk = _coordination_risk(unstable, report.propagation_effects)
        report.assessment = MultiEquilibriumAssessment(
            global_stability=global_stab,
            unstable_zones=unstable,
            recovering_zones=recovering,
            stabilized_zones=stabilized,
            coordination_risk=coord_risk,
        )

        # Governance: validate assessment.
        _, assess_violations = self._governance.validate_assessment(report.assessment)
        report.governance_violations.extend(assess_violations)

        # 8. Human review requirement.
        report.review_required = self._governance.review_required(report.zones, confidence)

        return report
