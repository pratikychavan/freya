"""freya/partitioning/coupling.py

Adaptive Partition Coupling Engine.

Manages coupling strength between operational partitions to reduce
destabilizing propagation and increase stabilization isolation.
"""
from __future__ import annotations

from freya.partitioning.models import (
    CouplingStrength,
    OperationalPartition,
    PartitionCouplingState,
    PropagationRisk,
)

# ---------------------------------------------------------------------------
# Default coupling rules between partition types.
# (source_type, target_type) → (coupling_strength, propagation_risk, dependency note)
# ---------------------------------------------------------------------------
_DEFAULT_COUPLINGS: dict[tuple[str, str], dict] = {
    ("incident_coordination", "governance_escalation"): {
        "coupling_strength": "tight",
        "propagation_risk": "high",
        "stabilization_dependency": "Governance review decisions directly gate incident escalation resolution.",
    },
    ("incident_coordination", "retry_amplification"): {
        "coupling_strength": "moderate",
        "propagation_risk": "moderate",
        "stabilization_dependency": "Incident workflows frequently trigger retry loops that must be contained.",
    },
    ("governance_escalation", "retry_amplification"): {
        "coupling_strength": "tight",
        "propagation_risk": "high",
        "stabilization_dependency": "Governance congestion is a primary driver of retry amplification.",
    },
    ("governance_escalation", "optimization_backlog"): {
        "coupling_strength": "loose",
        "propagation_risk": "low",
        "stabilization_dependency": "Governance recovery slightly accelerates optimization resumption.",
    },
    ("retry_amplification", "optimization_backlog"): {
        "coupling_strength": "moderate",
        "propagation_risk": "moderate",
        "stabilization_dependency": "Sustained retry load delays optimization queue processing.",
    },
    ("optimization_backlog", "recovery_surge"): {
        "coupling_strength": "loose",
        "propagation_risk": "low",
        "stabilization_dependency": "Optimization restoration aids recovery path throughput.",
    },
    ("recovery_surge", "incident_coordination"): {
        "coupling_strength": "moderate",
        "propagation_risk": "moderate",
        "stabilization_dependency": "Recovery surge activity feeds back into incident coordination pipelines.",
    },
}

# Coupling adjustments based on active pressure and confidence.
_WEAKENING_RULES: list[dict] = [
    {
        "source_type": "optimization_backlog",
        "target_type": "retry_amplification",
        "condition": "optimization_pressure_high",
        "new_strength": "loose",
        "new_risk": "low",
        "reason": "Weakening optimization↔retry coupling to prevent backlog pressure spreading into retry handling.",
    },
    {
        "source_type": "governance_escalation",
        "target_type": "incident_coordination",
        "condition": "governance_isolated",
        "new_strength": "isolated",
        "new_risk": "low",
        "reason": "Governance partition isolated to contain escalation pressure locally during stabilization.",
    },
]


class AdaptivePartitionCouplingEngine:
    """Computes and adjusts coupling states between operational partitions."""

    def compute_couplings(
        self,
        partitions: list[OperationalPartition],
        active_conditions: set[str] | None = None,
    ) -> list[PartitionCouplingState]:
        """Return coupling states for all pairs of active partitions.

        Args:
            partitions: Active operational partitions.
            active_conditions: Optional set of condition flags for adaptive weakening.
        """
        active_conditions = active_conditions or set()
        couplings: list[PartitionCouplingState] = []
        for i, src in enumerate(partitions):
            for tgt in partitions[i + 1:]:
                key = (src.partition_type, tgt.partition_type)
                rev_key = (tgt.partition_type, src.partition_type)
                template = _DEFAULT_COUPLINGS.get(key) or _DEFAULT_COUPLINGS.get(rev_key)
                if template is None:
                    template = {
                        "coupling_strength": "loose",
                        "propagation_risk": "low",
                        "stabilization_dependency": "No direct dependency identified.",
                    }
                strength: CouplingStrength = template["coupling_strength"]
                risk: PropagationRisk = template["propagation_risk"]

                # Apply weakening rules.
                for rule in _WEAKENING_RULES:
                    pair_match = (
                        src.partition_type == rule["source_type"]
                        and tgt.partition_type == rule["target_type"]
                    ) or (
                        tgt.partition_type == rule["source_type"]
                        and src.partition_type == rule["target_type"]
                    )
                    if pair_match and rule["condition"] in active_conditions:
                        strength = rule["new_strength"]
                        risk = rule["new_risk"]

                couplings.append(
                    PartitionCouplingState(
                        source_partition=src.partition_name,
                        target_partition=tgt.partition_name,
                        coupling_strength=strength,
                        propagation_risk=risk,
                        stabilization_dependency=template["stabilization_dependency"],
                    )
                )
        return couplings

    def high_risk_couplings(
        self, couplings: list[PartitionCouplingState]
    ) -> list[PartitionCouplingState]:
        return [c for c in couplings if c.propagation_risk == "high"]

    def recommend_weakening(
        self,
        coupling: PartitionCouplingState,
    ) -> str:
        """Return a plain-language coupling reduction recommendation."""
        if coupling.coupling_strength == "isolated":
            return f"'{coupling.source_partition}' is already isolated from '{coupling.target_partition}'."
        if coupling.propagation_risk == "high":
            return (
                f"Reduce coupling between '{coupling.source_partition}' and "
                f"'{coupling.target_partition}' from '{coupling.coupling_strength}' to 'loose' "
                "to limit high-risk propagation."
            )
        return (
            f"Coupling between '{coupling.source_partition}' and "
            f"'{coupling.target_partition}' is within tolerable bounds."
        )
