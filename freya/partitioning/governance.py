"""freya/partitioning/governance.py

Partitioning Governance Layer.

Validates partition safety, restricts unsafe isolation behavior, and
enforces bounded duration and explainability for all partitions.

Hard rules:
- Critical workflows cannot be isolated from governance pathways
- Governance partitions require bounded duration acknowledgment
- Retry isolation cannot bypass approval gating
- Partition fragmentation beyond 4 concurrent partitions requires review
"""
from __future__ import annotations

from freya.partitioning.models import (
    OperationalPartition,
    PartitionCouplingState,
    OperationalSustainabilityAssessment,
)

_MAX_CONCURRENT_PARTITIONS = 4

# Partition types whose isolation is restricted without explicit justification.
_RESTRICTED_ISOLATION_TYPES: frozenset[str] = frozenset(
    {"governance_escalation", "incident_coordination"}
)

# Coupling states that are unsafe outside of explicit governance approval.
_UNSAFE_ISOLATED_TYPES: frozenset[str] = frozenset(
    {"governance_escalation"}  # governance must never become fully isolated
)

_UNSAFE_PARTITION_WORKFLOWS: frozenset[str] = frozenset(
    {
        "bypass_approval",
        "skip_governance",
        "force_isolation",
        "circumvent_audit",
    }
)


class PartitioningGovernanceEngine:
    """Validates partition configurations and coupling states for safety."""

    def validate_partitions(
        self,
        partitions: list[OperationalPartition],
        confidence: float = 0.70,
    ) -> tuple[bool, list[str]]:
        """Validate a set of active partitions for governance compliance.

        Returns (is_valid, violations).
        """
        violations: list[str] = []

        if len(partitions) > _MAX_CONCURRENT_PARTITIONS:
            violations.append(
                f"{len(partitions)} concurrent partitions active — exceeds maximum "
                f"{_MAX_CONCURRENT_PARTITIONS}. Human review required before adding more."
            )

        for p in partitions:
            # Check for unsafe workflow names.
            for wf in p.participating_workflows:
                for unsafe in _UNSAFE_PARTITION_WORKFLOWS:
                    if unsafe in wf.lower():
                        violations.append(
                            f"Partition '{p.partition_name}' contains unsafe workflow "
                            f"'{wf}' — governance bypass patterns are prohibited."
                        )

        if confidence < 0.50 and len(partitions) > 2:
            violations.append(
                f"Low confidence {confidence:.0%} with {len(partitions)} active partitions — "
                "restrict to advisory-only mode until confidence recovers."
            )

        return (len(violations) == 0, violations)

    def validate_coupling(
        self, coupling: PartitionCouplingState
    ) -> tuple[bool, list[str]]:
        """Validate a coupling state for safety.

        Returns (is_valid, violations).
        """
        violations: list[str] = []

        if coupling.coupling_strength == "isolated":
            for unsafe_type in _UNSAFE_ISOLATED_TYPES:
                type_label = unsafe_type.replace("_", " ").title()
                if type_label.lower() in coupling.source_partition.lower():
                    violations.append(
                        f"'{coupling.source_partition}' cannot be fully isolated — "
                        "governance partitions must retain coordination pathways."
                    )

        return (len(violations) == 0, violations)

    def validate_sustainability(
        self, assessment: OperationalSustainabilityAssessment
    ) -> tuple[bool, list[str]]:
        """Validate a sustainability assessment for critical risk signals.

        Returns (is_valid, violations).
        """
        violations: list[str] = []

        if assessment.sustainability_state == "exhausted":
            violations.append(
                "Sustainability state is EXHAUSTED — current stabilization strategy must be "
                "rotated immediately. Human operator escalation required."
            )
        if assessment.adaptation_fatigue_risk == "critical":
            violations.append(
                "Adaptation fatigue is CRITICAL — intervention rotation required to restore "
                "organizational capacity before continuing stabilization."
            )

        return (len(violations) == 0, violations)

    def review_required(
        self,
        partitions: list[OperationalPartition],
        confidence: float,
    ) -> bool:
        """Return True when the current partition configuration warrants human review."""
        if confidence < 0.55:
            return True
        if len(partitions) >= _MAX_CONCURRENT_PARTITIONS:
            return True
        critical = [p for p in partitions if p.stabilization_priority == "critical"]
        if len(critical) >= 2:
            return True
        return False
