"""examples/adaptive_partitioning_demo.py

Adaptive Organizational Partitioning Layer — Scenarios EH through EN.

Each scenario is self-contained and exercises a distinct aspect of the
freya.partitioning module. No external services required.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from freya.partitioning import (
    AdaptivePartitionCouplingEngine,
    AdaptivePartitioningPipeline,
    OperationalClusterDetectionEngine,
    OperationalPressureMigrationEngine,
    OperationalSustainabilityEngine,
    PartitioningGovernanceEngine,
    render_operational_partition,
    render_partition_coupling,
    render_pressure_migration,
    render_sustainability_assessment,
)
from freya.partitioning.models import OperationalPartition


def divider(label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}\n")


# ---------------------------------------------------------------------------
# Scenario EH — Incident Coordination Partition
# ---------------------------------------------------------------------------
def scenario_eh() -> None:
    divider("Scenario EH — Incident Coordination Partition (Temporary Cluster)")

    detector = OperationalClusterDetectionEngine()

    signals = {"escalation_active", "governance_review_surge", "retry_spike"}
    partitions = detector.detect(signals, confidence=0.78)

    print(f"Active signals:        {signals}")
    print(f"Partitions formed:     {len(partitions)}")
    print()
    for p in partitions:
        print(render_operational_partition(p))
        print()

    print(
        "Insight: Incident coordination and retry amplification partitions are formed\n"
        "         automatically from active signals. Each is temporary and bounded.\n"
        "         No global restructuring occurs.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EI — Retry Amplification Cluster
# ---------------------------------------------------------------------------
def scenario_ei() -> None:
    divider("Scenario EI — Retry Amplification Cluster (Localized Instability Isolated)")

    detector = OperationalClusterDetectionEngine()

    signals = {"retry_spike", "reasoning_saturation"}
    partitions = detector.detect(signals, confidence=0.72)

    print(f"Active signals: {signals}")
    print(f"Partitions:     {len(partitions)}")
    print()
    for p in partitions:
        print(render_operational_partition(p))

    print(
        "\nInsight: Retry amplification is isolated into its own partition.\n"
        "         Reasoning saturation is captured as context within the partition —\n"
        "         not propagated globally. Local containment prevents cross-zone spread.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EJ — Adaptive Coupling Reduction
# ---------------------------------------------------------------------------
def scenario_ej() -> None:
    divider("Scenario EJ — Adaptive Coupling Reduction (Optimization Coupling Weakened)")

    detector = OperationalClusterDetectionEngine()
    coupler = AdaptivePartitionCouplingEngine()

    # Form partitions that include a retry + optimization pair.
    signals = {"retry_spike", "optimization_suspended", "governance_congestion"}
    partitions = detector.detect(signals, confidence=0.75)

    # Default couplings.
    default_couplings = coupler.compute_couplings(partitions)
    print(f"Default couplings: {len(default_couplings)}")
    for c in default_couplings:
        print(f"  {c.source_partition} ↔ {c.target_partition}: {c.coupling_strength} / risk={c.propagation_risk}")

    # Adaptive weakening: optimization pressure high.
    weakened_couplings = coupler.compute_couplings(
        partitions, active_conditions={"optimization_pressure_high"}
    )
    print(f"\nWith optimization_pressure_high condition:")
    for c in weakened_couplings:
        print(f"  {c.source_partition} ↔ {c.target_partition}: {c.coupling_strength} / risk={c.propagation_risk}")

    high_risk = coupler.high_risk_couplings(weakened_couplings)
    print(f"\nHigh-risk couplings remaining: {len(high_risk)}")
    for c in high_risk:
        print(f"  → {coupler.recommend_weakening(c)}")
        print(render_partition_coupling(c))

    print(
        "\nInsight: Coupling is weakened adaptively when conditions indicate elevated\n"
        "         optimization pressure. This reduces cross-partition propagation risk\n"
        "         without permanently restructuring organizational relationships.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EK — Pressure Migration Tracking
# ---------------------------------------------------------------------------
def scenario_ek() -> None:
    divider("Scenario EK — Pressure Migration Tracking (Governance Stabilization → Delegation)")

    detector = OperationalClusterDetectionEngine()
    migration_engine = OperationalPressureMigrationEngine()

    # Active partitions include both governance escalation and retry amplification.
    active_signals = {
        "governance_congestion", "retry_spike", "optimization_suspended", "recovery_surge"
    }
    active_partitions = detector.detect(active_signals, confidence=0.78)

    print(f"Active partitions: {[p.partition_name for p in active_partitions]}")
    print()

    # Governance escalation just stabilized — what pressure migrates?
    stabilized_types = {"governance_escalation"}
    events = migration_engine.detect_migrations(
        active_partitions=active_partitions,
        stabilized_partition_types=stabilized_types,
    )

    print(f"Migration events detected: {len(events)}")
    for event in events:
        print()
        print(render_pressure_migration(event))

    best = migration_engine.highest_confidence_migration(events)
    if best:
        print(f"\nHighest-confidence migration: {best.source_partition} → {best.target_partition} ({best.confidence_score:.0%})")

    print(
        "\nInsight: Governance stabilization does not end instability — it migrates it.\n"
        "         The engine tracks where pressure moves so recovery can be pre-positioned.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EL — Sustainability Fatigue Detection
# ---------------------------------------------------------------------------
def scenario_el() -> None:
    divider("Scenario EL — Sustainability Fatigue Detection (Long-term Compression)")

    sustainability = OperationalSustainabilityEngine()
    detector = OperationalClusterDetectionEngine()

    partitions = detector.detect(
        {"retry_spike", "governance_congestion", "escalation_active", "governance_review_surge"},
        confidence=0.75,
    )

    # Short-term: 2 cycles.
    short_term = sustainability.assess(
        active_interventions=["reasoning_compression", "governance_batching", "optimization_suspended"],
        active_partitions=partitions,
        duration_cycles=2,
    )
    print("Short-term (2 cycles):")
    print(render_sustainability_assessment(short_term))

    # Long-term: 8 cycles.
    long_term = sustainability.assess(
        active_interventions=["reasoning_compression", "governance_batching", "optimization_suspended"],
        active_partitions=partitions,
        duration_cycles=8,
    )
    print("\nLong-term (8 cycles):")
    print(render_sustainability_assessment(long_term))

    breakdown = sustainability.fatigue_breakdown(
        ["reasoning_compression", "governance_batching", "optimization_suspended"]
    )
    print("\nFatigue breakdown per intervention:")
    for name, score in breakdown.items():
        print(f"  {name:<30} {score:.2f}")

    print(
        "\nInsight: The same interventions that are sustainable short-term become fatiguing\n"
        "         at 8 cycles. Duration is a first-class input to sustainability cognition.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EM — Unsafe Partition Isolation Blocked
# ---------------------------------------------------------------------------
def scenario_em() -> None:
    divider("Scenario EM — Unsafe Partition Isolation Blocked")

    governance = PartitioningGovernanceEngine()

    # Try to create more than the max allowed concurrent partitions.
    partitions = [
        OperationalPartition(
            partition_name="Incident Coordination Partition",
            partition_type="incident_coordination",
            participating_workflows=["incident_escalation_pipeline"],
            dominant_pressure="Escalation surge",
            stabilization_priority="critical",
        ),
        OperationalPartition(
            partition_name="Governance Escalation Partition",
            partition_type="governance_escalation",
            participating_workflows=["governance_approval_pipeline"],
            dominant_pressure="Approval backlog",
            stabilization_priority="critical",
        ),
        OperationalPartition(
            partition_name="Retry Amplification Partition",
            partition_type="retry_amplification",
            participating_workflows=["retry_coordination_handler"],
            dominant_pressure="Retry churn",
            stabilization_priority="high",
        ),
        OperationalPartition(
            partition_name="Optimization Backlog Partition",
            partition_type="optimization_backlog",
            participating_workflows=["deferred_optimization_queue"],
            dominant_pressure="Optimization backlog",
            stabilization_priority="moderate",
        ),
        OperationalPartition(
            partition_name="Recovery Surge Partition",
            partition_type="recovery_surge",
            participating_workflows=["incident_recovery_coordinator"],
            dominant_pressure="Recovery overload",
            stabilization_priority="high",
        ),
    ]

    valid, violations = governance.validate_partitions(partitions, confidence=0.72)
    print(f"Partitions proposed: {len(partitions)}")
    print(f"Governance valid: {valid}")
    if violations:
        print("Violations:")
        for v in violations:
            print(f"  ⚠  {v}")

    review = governance.review_required(partitions, confidence=0.72)
    print(f"\nHuman review required: {review}")

    print(
        "\nInsight: Fragmenting into 5 concurrent partitions is blocked by governance.\n"
        "         The limit of 4 prevents uncontrolled partition proliferation.\n"
        "         Human review is required before additional partitions are activated.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EN — Executive Adaptive Partition Summary (Full Pipeline)
# ---------------------------------------------------------------------------
def scenario_en() -> None:
    divider("Scenario EN — Executive Adaptive Partition Summary (Full Pipeline)")

    pipeline = AdaptivePartitioningPipeline()

    result = pipeline.run(
        active_signals={
            "retry_spike",
            "governance_congestion",
            "escalation_active",
            "governance_review_surge",
        },
        active_interventions=[
            "batching_applied",
            "smoothing_applied",
            "reasoning_compression",
        ],
        stabilized_partition_types={"governance_escalation"},
        active_conditions=set(),
        confidence=0.76,
        duration_cycles=3,
    )

    report = result["report"]
    print(f"Partitions formed:    {report.partition_count}")
    print(f"Migration events:     {len(report.migration_events)}")
    print(f"High-risk couplings:  {len(report.high_risk_couplings)}")
    print(f"Review required:      {result['review_required']}")
    print(f"Governance safe:      {result['is_safe']}")
    if report.sustainability:
        print(f"Sustainability:       {report.sustainability.sustainability_state}")
        print(f"Fatigue risk:         {report.sustainability.adaptation_fatigue_risk}")
    print()
    print(result["render"])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    print("\nFreya SDK — Adaptive Organizational Partitioning Demo (EH–EN)")
    print("=" * 72)

    scenario_eh()
    scenario_ei()
    scenario_ej()
    scenario_ek()
    scenario_el()
    scenario_em()
    scenario_en()

    print("\nAll adaptive partitioning scenarios completed successfully.\n")


if __name__ == "__main__":
    main()
