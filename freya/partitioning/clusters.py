"""freya/partitioning/clusters.py

Operational Cluster Detection Engine.

Detects workflow coordination clusters — localized pressure concentrations,
escalation groupings, and retry amplification hotspots.
All detection is bounded to operational telemetry.
"""
from __future__ import annotations

from freya.partitioning.models import OperationalPartition, PartitionType, StabilizationPriority

# ---------------------------------------------------------------------------
# Cluster detection rules
# Each rule maps a set of signal conditions to a partition type.
# ---------------------------------------------------------------------------
_CLUSTER_RULES: list[dict] = [
    {
        "name": "incident_coordination_cluster",
        "partition_type": "incident_coordination",
        "partition_name": "Incident Coordination Partition",
        "required_signals": {"escalation_active", "governance_review_surge"},
        "optional_signals": {"retry_spike", "delegation_contention"},
        "dominant_pressure": "Escalation pipeline pressure and governance review surge",
        "stabilization_priority": "critical",
        "workflows": [
            "incident_escalation_pipeline",
            "governance_review_surge",
            "escalation_retry_handler",
        ],
    },
    {
        "name": "retry_amplification_cluster",
        "partition_type": "retry_amplification",
        "partition_name": "Retry Amplification Partition",
        "required_signals": {"retry_spike"},
        "optional_signals": {"reasoning_saturation", "governance_congestion"},
        "dominant_pressure": "Retry churn saturating reasoning pool capacity",
        "stabilization_priority": "high",
        "workflows": [
            "retry_coordination_handler",
            "reasoning_pool_arbiter",
            "contention_monitor",
        ],
    },
    {
        "name": "governance_escalation_cluster",
        "partition_type": "governance_escalation",
        "partition_name": "Governance Escalation Partition",
        "required_signals": {"governance_congestion"},
        "optional_signals": {"escalation_active", "approval_backlog"},
        "dominant_pressure": "Governance approval queue backlog and congestion",
        "stabilization_priority": "high",
        "workflows": [
            "governance_approval_pipeline",
            "batching_coordinator",
            "approval_backlog_handler",
        ],
    },
    {
        "name": "optimization_backlog_cluster",
        "partition_type": "optimization_backlog",
        "partition_name": "Optimization Backlog Partition",
        "required_signals": {"optimization_suspended"},
        "optional_signals": {"reasoning_saturation", "backlog_accumulating"},
        "dominant_pressure": "Accumulated optimization backlog under sustained suspension",
        "stabilization_priority": "moderate",
        "workflows": [
            "deferred_optimization_queue",
            "optimization_resume_coordinator",
            "backlog_processor",
        ],
    },
    {
        "name": "recovery_surge_cluster",
        "partition_type": "recovery_surge",
        "partition_name": "Recovery Surge Partition",
        "required_signals": {"recovery_surge"},
        "optional_signals": {"incident_escalation", "degradation_onset"},
        "dominant_pressure": "Recovery coordination overload from concurrent incident resolution",
        "stabilization_priority": "high",
        "workflows": [
            "incident_recovery_coordinator",
            "restoration_pipeline",
            "recovery_audit_handler",
        ],
    },
]


class OperationalClusterDetectionEngine:
    """Detects active operational clusters from a set of operational signals."""

    def detect(
        self,
        active_signals: set[str],
        confidence: float = 0.70,
    ) -> list[OperationalPartition]:
        """Return all clusters whose required signals are present in `active_signals`.

        Args:
            active_signals: Set of string signal names currently active.
            confidence: Operational confidence; partitions are only formed when
                        confidence ≥ 0.50.

        Returns:
            List of OperationalPartition objects (may be empty).
        """
        if confidence < 0.50:
            return []

        partitions: list[OperationalPartition] = []
        for rule in _CLUSTER_RULES:
            if not rule["required_signals"].issubset(active_signals):
                continue

            # Extend workflow list if optional signals add context.
            workflows = list(rule["workflows"])
            for sig in rule.get("optional_signals", set()):
                if sig in active_signals and sig not in workflows:
                    workflows.append(sig + "_handler")

            partitions.append(
                OperationalPartition(
                    partition_name=rule["partition_name"],
                    partition_type=rule["partition_type"],
                    participating_workflows=workflows,
                    dominant_pressure=rule["dominant_pressure"],
                    stabilization_priority=rule["stabilization_priority"],
                )
            )
        return partitions

    def known_signals(self) -> set[str]:
        """Return the full set of signals referenced across all cluster rules."""
        signals: set[str] = set()
        for rule in _CLUSTER_RULES:
            signals |= rule["required_signals"]
            signals |= rule.get("optional_signals", set())
        return signals
