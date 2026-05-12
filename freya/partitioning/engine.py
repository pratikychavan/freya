"""freya/partitioning/engine.py

Adaptive Organizational Partitioning Engine — central coordinator.

Orchestrates: cluster detection → coupling → migration → sustainability → governance.
All partitioning is bounded, explainable, and governance-approved.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from freya.partitioning.clusters import OperationalClusterDetectionEngine
from freya.partitioning.coupling import AdaptivePartitionCouplingEngine
from freya.partitioning.governance import PartitioningGovernanceEngine
from freya.partitioning.migration import OperationalPressureMigrationEngine
from freya.partitioning.models import (
    OperationalPartition,
    OperationalSustainabilityAssessment,
    PartitionCouplingState,
    PressureMigrationEvent,
)
from freya.partitioning.sustainability import OperationalSustainabilityEngine


@dataclass
class AdaptivePartitioningReport:
    """Complete output from an adaptive organizational partitioning analysis."""

    active_signals: set[str]
    active_interventions: list[str]
    confidence: float
    duration_cycles: int

    partitions: list[OperationalPartition] = field(default_factory=list)
    couplings: list[PartitionCouplingState] = field(default_factory=list)
    migration_events: list[PressureMigrationEvent] = field(default_factory=list)
    sustainability: OperationalSustainabilityAssessment | None = None
    governance_violations: list[str] = field(default_factory=list)
    review_required: bool = False

    @property
    def is_safe(self) -> bool:
        return len(self.governance_violations) == 0

    @property
    def high_risk_couplings(self) -> list[PartitionCouplingState]:
        return [c for c in self.couplings if c.propagation_risk == "high"]

    @property
    def partition_count(self) -> int:
        return len(self.partitions)


class AdaptiveOrganizationalPartitioningEngine:
    """Coordinates adaptive partitioning, coupling, migration, and sustainability."""

    def __init__(self) -> None:
        self._clusters = OperationalClusterDetectionEngine()
        self._coupling = AdaptivePartitionCouplingEngine()
        self._migration = OperationalPressureMigrationEngine()
        self._sustainability = OperationalSustainabilityEngine()
        self._governance = PartitioningGovernanceEngine()

    def analyze(
        self,
        active_signals: set[str],
        active_interventions: list[str],
        stabilized_partition_types: set[str] | None = None,
        active_conditions: set[str] | None = None,
        confidence: float = 0.70,
        duration_cycles: int = 1,
    ) -> AdaptivePartitioningReport:
        """Run a full adaptive partitioning analysis.

        Args:
            active_signals: Operational signal names currently active
                            (e.g. {"retry_spike", "governance_congestion"}).
            active_interventions: Interventions currently in effect.
            stabilized_partition_types: Partition types that have recently stabilized
                                         (triggers migration analysis).
            active_conditions: Condition flags for adaptive coupling weakening
                                (e.g. {"optimization_pressure_high"}).
            confidence: Operational confidence in [0.0, 1.0].
            duration_cycles: Consecutive cycles the current strategy has been active.

        Returns:
            AdaptivePartitioningReport with all sub-analyses populated.
        """
        stabilized_partition_types = stabilized_partition_types or set()
        active_conditions = active_conditions or set()

        report = AdaptivePartitioningReport(
            active_signals=set(active_signals),
            active_interventions=list(active_interventions),
            confidence=confidence,
            duration_cycles=duration_cycles,
        )

        # 1. Detect operational clusters → form partitions.
        report.partitions = self._clusters.detect(active_signals, confidence=confidence)

        # 2. Governance: validate partitions.
        valid_p, p_violations = self._governance.validate_partitions(
            report.partitions, confidence=confidence
        )
        report.governance_violations.extend(p_violations)

        # 3. Compute partition couplings.
        report.couplings = self._coupling.compute_couplings(
            report.partitions, active_conditions=active_conditions
        )

        # Governance: validate each coupling.
        for coupling in report.couplings:
            _, c_violations = self._governance.validate_coupling(coupling)
            report.governance_violations.extend(c_violations)

        # 4. Detect pressure migration events.
        report.migration_events = self._migration.detect_migrations(
            active_partitions=report.partitions,
            stabilized_partition_types=stabilized_partition_types,
        )

        # 5. Sustainability assessment.
        report.sustainability = self._sustainability.assess(
            active_interventions=active_interventions,
            active_partitions=report.partitions,
            duration_cycles=duration_cycles,
        )

        # Governance: validate sustainability.
        _, s_violations = self._governance.validate_sustainability(report.sustainability)
        report.governance_violations.extend(s_violations)

        # 6. Human review requirement.
        report.review_required = self._governance.review_required(
            report.partitions, confidence
        )

        return report
