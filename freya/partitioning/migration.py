"""freya/partitioning/migration.py

Operational Pressure Migration Engine.

Tracks movement of operational pressure between partitions, detects
shifting instability centers, and coordinates stabilization handoffs.
"""
from __future__ import annotations

from freya.partitioning.models import OperationalPartition, PressureMigrationEvent

# ---------------------------------------------------------------------------
# Migration pattern catalog
# Maps (stabilized_partition_type, destabilized_target_type) → event template.
# ---------------------------------------------------------------------------
_MIGRATION_PATTERNS: list[dict] = [
    {
        "trigger": "governance_escalation_stabilized",
        "source_type": "governance_escalation",
        "target_type": "retry_amplification",
        "migration_reason": (
            "Governance stabilization reduced approval backlog, but deferred retries now "
            "resume — concentrating retry load into the retry amplification partition."
        ),
        "projected_effect": (
            "Retry amplification partition experiences a temporary pressure surge as "
            "previously held-back retries flush through the reasoning pool."
        ),
        "confidence": 0.75,
    },
    {
        "trigger": "governance_escalation_stabilized",
        "source_type": "governance_escalation",
        "target_type": "optimization_backlog",
        "migration_reason": (
            "Governance recovery releases deferred optimization tasks, increasing "
            "optimization backlog partition throughput demand."
        ),
        "projected_effect": (
            "Optimization backlog partition load increases as governance-gated optimization "
            "tasks re-enter the processing queue."
        ),
        "confidence": 0.65,
    },
    {
        "trigger": "retry_amplification_stabilized",
        "source_type": "retry_amplification",
        "target_type": "recovery_surge",
        "migration_reason": (
            "Retry suppression reduces reasoning pool pressure, but recovery coordination "
            "for previously failed workflows increases recovery zone load."
        ),
        "projected_effect": (
            "Recovery surge partition experiences elevated throughput demand as suppressed-retry "
            "workflows re-enter recovery coordination."
        ),
        "confidence": 0.70,
    },
    {
        "trigger": "optimization_backlog_restored",
        "source_type": "optimization_backlog",
        "target_type": "retry_amplification",
        "migration_reason": (
            "Optimization restoration increases reasoning pool utilization, raising the "
            "risk of retry amplification from contention."
        ),
        "projected_effect": (
            "Retry amplification partition may see increased pressure as optimization "
            "competes for reasoning pool capacity."
        ),
        "confidence": 0.68,
    },
    {
        "trigger": "incident_coordination_resolved",
        "source_type": "incident_coordination",
        "target_type": "governance_escalation",
        "migration_reason": (
            "Incident resolution generates post-incident governance review demand, "
            "temporarily elevating governance escalation load."
        ),
        "projected_effect": (
            "Governance escalation partition experiences a post-incident load spike "
            "from review and audit requirements."
        ),
        "confidence": 0.72,
    },
]


class OperationalPressureMigrationEngine:
    """Tracks pressure movement between partitions as stabilization progresses."""

    def detect_migrations(
        self,
        active_partitions: list[OperationalPartition],
        stabilized_partition_types: set[str],
    ) -> list[PressureMigrationEvent]:
        """Return migration events for each stabilized partition.

        Args:
            active_partitions: Currently active operational partitions.
            stabilized_partition_types: Partition types that have just stabilized.
        """
        active_types = {p.partition_type: p.partition_name for p in active_partitions}
        events: list[PressureMigrationEvent] = []

        for pattern in _MIGRATION_PATTERNS:
            if pattern["source_type"] not in stabilized_partition_types:
                continue
            target_type = pattern["target_type"]
            # Only report migration if the target partition is actually active.
            if target_type not in active_types:
                continue
            source_name = next(
                (p.partition_name for p in active_partitions
                 if p.partition_type == pattern["source_type"]),
                pattern["source_type"].replace("_", " ").title(),
            )
            events.append(
                PressureMigrationEvent(
                    source_partition=source_name,
                    target_partition=active_types[target_type],
                    migration_reason=pattern["migration_reason"],
                    projected_operational_effect=pattern["projected_effect"],
                    confidence_score=pattern["confidence"],
                )
            )
        return events

    def highest_confidence_migration(
        self, events: list[PressureMigrationEvent]
    ) -> PressureMigrationEvent | None:
        """Return the migration event with the highest confidence score."""
        if not events:
            return None
        return max(events, key=lambda e: e.confidence_score)
