"""freya/partitioning/__init__.py

Public API for the Adaptive Organizational Partitioning Layer.

Example::

    from freya.partitioning import AdaptivePartitioningPipeline

    result = AdaptivePartitioningPipeline().run(
        active_signals={"retry_spike", "governance_congestion"},
        active_interventions=["batching_applied", "smoothing_applied"],
        confidence=0.75,
        duration_cycles=3,
    )
    print(result["render"])
"""
from __future__ import annotations

from freya.partitioning.clusters import OperationalClusterDetectionEngine
from freya.partitioning.coupling import AdaptivePartitionCouplingEngine
from freya.partitioning.engine import (
    AdaptiveOrganizationalPartitioningEngine,
    AdaptivePartitioningReport,
)
from freya.partitioning.governance import PartitioningGovernanceEngine
from freya.partitioning.migration import OperationalPressureMigrationEngine
from freya.partitioning.models import (
    OperationalPartition,
    OperationalSustainabilityAssessment,
    PartitionCouplingState,
    PressureMigrationEvent,
)
from freya.partitioning.rendering import (
    render_operational_partition,
    render_partition_coupling,
    render_pressure_migration,
    render_sustainability_assessment,
)
from freya.partitioning.sustainability import OperationalSustainabilityEngine


class AdaptivePartitioningPipeline:
    """Façade that orchestrates the full adaptive organizational partitioning pipeline."""

    def __init__(self) -> None:
        self._engine = AdaptiveOrganizationalPartitioningEngine()

    def run(
        self,
        active_signals: set[str],
        active_interventions: list[str],
        stabilized_partition_types: set[str] | None = None,
        active_conditions: set[str] | None = None,
        confidence: float = 0.70,
        duration_cycles: int = 1,
    ) -> dict:
        """Execute the full partitioning analysis and return a structured result.

        The returned dict includes:
        - ``report``          — :class:`AdaptivePartitioningReport`
        - ``review_required`` — bool
        - ``is_safe``         — bool (no governance violations)
        - ``render``          — human-readable multi-section string
        """
        report: AdaptivePartitioningReport = self._engine.analyze(
            active_signals=active_signals,
            active_interventions=active_interventions,
            stabilized_partition_types=stabilized_partition_types,
            active_conditions=active_conditions,
            confidence=confidence,
            duration_cycles=duration_cycles,
        )

        render_sections: list[str] = []

        for partition in report.partitions:
            render_sections.append(render_operational_partition(partition))

        for coupling in report.high_risk_couplings:
            render_sections.append(render_partition_coupling(coupling))

        for event in report.migration_events:
            render_sections.append(render_pressure_migration(event))

        if report.sustainability is not None:
            render_sections.append(render_sustainability_assessment(report.sustainability))

        if report.governance_violations:
            block = (
                "┌─ Governance Observations ──────────────────────────────────────────┐\n"
                + "\n".join(f"│  ⚠  {v}" for v in report.governance_violations)
                + "\n└────────────────────────────────────────────────────────────────────┘"
            )
            render_sections.append(block)

        return {
            "report": report,
            "review_required": report.review_required,
            "is_safe": report.is_safe,
            "render": "\n\n".join(render_sections),
        }


__all__ = [
    "AdaptivePartitioningPipeline",
    "AdaptiveOrganizationalPartitioningEngine",
    "AdaptivePartitioningReport",
    "OperationalClusterDetectionEngine",
    "AdaptivePartitionCouplingEngine",
    "OperationalPressureMigrationEngine",
    "OperationalSustainabilityEngine",
    "PartitioningGovernanceEngine",
    "OperationalPartition",
    "PartitionCouplingState",
    "PressureMigrationEvent",
    "OperationalSustainabilityAssessment",
    "render_operational_partition",
    "render_partition_coupling",
    "render_pressure_migration",
    "render_sustainability_assessment",
]
