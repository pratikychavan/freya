"""freya/equilibrium/__init__.py

Public API for the Multi-Equilibrium Operational Cognition Layer.

Example::

    from freya.equilibrium import MultiEquilibriumPipeline

    result = MultiEquilibriumPipeline().run(
        pressure_map={
            "governance": 0.40,
            "reasoning":  0.72,
            "optimization": 0.55,
        },
        confidence=0.75,
    )
    print(result["render"])
"""
from __future__ import annotations

from freya.equilibrium.balancing import OperationalEquilibriumBalancingEngine
from freya.equilibrium.engine import MultiEquilibriumOperationalEngine, MultiEquilibriumReport
from freya.equilibrium.governance import EquilibriumGovernanceEngine
from freya.equilibrium.models import (
    MultiEquilibriumAssessment,
    OperationalEquilibriumZone,
    ZonePropagationEffect,
    ZoneRecoveryPlan,
)
from freya.equilibrium.propagation import CrossZonePropagationEngine
from freya.equilibrium.recovery import AsynchronousRecoveryCoordinationEngine
from freya.equilibrium.rendering import (
    render_cross_zone_propagation,
    render_multi_equilibrium_summary,
    render_recovery_plan,
    render_zone_state,
)
from freya.equilibrium.zones import OperationalZoneManagementEngine


class MultiEquilibriumPipeline:
    """Façade that orchestrates the full multi-equilibrium analysis pipeline."""

    def __init__(self) -> None:
        self._engine = MultiEquilibriumOperationalEngine()

    def run(
        self,
        pressure_map: dict[str, float],
        confidence: float = 0.70,
    ) -> dict:
        """Execute the full multi-equilibrium analysis and return a structured result.

        The returned dict includes:
        - ``report``          — :class:`MultiEquilibriumReport`
        - ``review_required`` — bool
        - ``global_stability``— str
        - ``render``          — human-readable multi-section string
        """
        report: MultiEquilibriumReport = self._engine.analyze(
            pressure_map=pressure_map,
            confidence=confidence,
        )

        render_sections: list[str] = []

        # Zone states
        zone_state_block = "┌─ Zone Equilibrium States ───────────────────────────────────────────┐\n"
        zone_state_block += "\n".join(render_zone_state(z) for z in report.zones.values())
        zone_state_block += "\n└─────────────────────────────────────────────────────────────────────┘"
        render_sections.append(zone_state_block)

        # Cross-zone propagation
        render_sections.append(render_cross_zone_propagation(report.propagation_effects))

        # Recovery plans (only for non-stable zones)
        for key, plan in report.recovery_plans.items():
            zone = report.zones.get(key)
            if zone and zone.equilibrium_state not in ("stabilized", "restored"):
                render_sections.append(render_recovery_plan(plan))

        # Executive summary
        if report.assessment is not None:
            render_sections.append(
                render_multi_equilibrium_summary(
                    report.assessment,
                    report.zones,
                    report.balancing_recommendations,
                )
            )

        if report.governance_violations:
            block = (
                "┌─ Governance Observations ──────────────────────────────────────────┐\n"
                + "\n".join(f"│  ⚠  {v}" for v in report.governance_violations)
                + "\n└────────────────────────────────────────────────────────────────────┘"
            )
            render_sections.append(block)

        global_stability = report.assessment.global_stability if report.assessment else "unknown"

        return {
            "report": report,
            "review_required": report.review_required,
            "global_stability": global_stability,
            "render": "\n\n".join(render_sections),
        }


__all__ = [
    "MultiEquilibriumPipeline",
    "MultiEquilibriumOperationalEngine",
    "MultiEquilibriumReport",
    "OperationalZoneManagementEngine",
    "CrossZonePropagationEngine",
    "AsynchronousRecoveryCoordinationEngine",
    "OperationalEquilibriumBalancingEngine",
    "EquilibriumGovernanceEngine",
    "OperationalEquilibriumZone",
    "ZonePropagationEffect",
    "ZoneRecoveryPlan",
    "MultiEquilibriumAssessment",
    "render_zone_state",
    "render_cross_zone_propagation",
    "render_recovery_plan",
    "render_multi_equilibrium_summary",
]
