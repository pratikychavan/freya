"""freya/topology/__init__.py

Organizational Topology Evolution Layer — public façade.

Entry point: OrganizationalTopologyPipeline.run(...)
"""
from __future__ import annotations

from freya.topology.engine import OrganizationalTopologyEvolutionEngine, TopologyEvolutionReport
from freya.topology.governance import TopologyGovernanceEngine
from freya.topology.lifecycle import TopologyLifecycleManagementEngine
from freya.topology.memory import OperationalTopologyMemoryEngine
from freya.topology.models import (
    OperationalMemoryRecord,
    OperationalTopologyPattern,
    TopologyEvolutionAssessment,
    TopologyLifecycleState,
)
from freya.topology.rendering import (
    render_lifecycle_state,
    render_operational_memory,
    render_sustainability_summary,
    render_topology_evolution_summary,
    render_topology_pattern,
)
from freya.topology.sustainability import LongHorizonOperationalSustainabilityEngine


class OrganizationalTopologyPipeline:
    """High-level façade for the Organizational Topology Evolution Layer."""

    def __init__(self) -> None:
        self._engine = OrganizationalTopologyEvolutionEngine()

    def run(
        self,
        topology_occurrences: dict[str, int],
        active_interventions: list[str] | None = None,
        confidence: float = 0.70,
        horizon_cycles: int = 5,
    ) -> dict:
        """Execute a full topology evolution pipeline.

        Parameters
        ----------
        topology_occurrences:
            Mapping of topology name → observed occurrence count.
        active_interventions:
            Active operational intervention identifiers.
        confidence:
            Analytical confidence score [0.0, 1.0].
        horizon_cycles:
            Forward-looking cycle horizon for sustainability.

        Returns
        -------
        dict with keys:
            "report"          — TopologyEvolutionReport (full structured output)
            "review_required" — bool
            "evolution_state" — str | None
            "render"          — str (formatted executive render)
        """
        report = self._engine.analyze(
            topology_occurrences=topology_occurrences,
            active_interventions=active_interventions or [],
            confidence=confidence,
            horizon_cycles=horizon_cycles,
        )

        render_sections: list[str] = []

        for pattern in report.patterns:
            render_sections.append(render_topology_pattern(pattern))

        for state in report.lifecycle_states.values():
            render_sections.append(render_lifecycle_state(state))

        if report.assessment:
            render_sections.append(render_topology_evolution_summary(report.assessment))

        render_sections.append(render_sustainability_summary(report.sustainability))

        if report.governance_violations:
            violation_block = "GOVERNANCE VIOLATIONS DETECTED:\n" + "\n".join(
                f"  - {v}" for v in report.governance_violations
            )
            render_sections.append(violation_block)

        return {
            "report": report,
            "review_required": report.review_required,
            "evolution_state": report.assessment.evolution_state if report.assessment else None,
            "render": "\n\n".join(render_sections),
        }


__all__ = [
    "OrganizationalTopologyPipeline",
    "OrganizationalTopologyEvolutionEngine",
    "TopologyEvolutionReport",
    "TopologyLifecycleManagementEngine",
    "OperationalTopologyMemoryEngine",
    "TopologyGovernanceEngine",
    "LongHorizonOperationalSustainabilityEngine",
    "OperationalTopologyPattern",
    "TopologyLifecycleState",
    "OperationalMemoryRecord",
    "TopologyEvolutionAssessment",
    "render_topology_pattern",
    "render_lifecycle_state",
    "render_operational_memory",
    "render_topology_evolution_summary",
    "render_sustainability_summary",
]
