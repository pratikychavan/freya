"""examples/organizational_topology_demo.py

Organizational Topology Evolution Layer — demonstration scenarios EO–EU.

These scenarios show how the Freya topology layer detects recurring
operational structures, tracks lifecycle maturity, surfaces historical memory,
and applies governance guardrails to topology evolution decisions.
"""
from __future__ import annotations

from freya.topology import OrganizationalTopologyPipeline
from freya.topology.governance import TopologyGovernanceEngine
from freya.topology.lifecycle import TopologyLifecycleManagementEngine
from freya.topology.memory import OperationalTopologyMemoryEngine
from freya.topology.models import OperationalTopologyPattern
from freya.topology.rendering import (
    render_lifecycle_state,
    render_operational_memory,
    render_sustainability_summary,
    render_topology_evolution_summary,
    render_topology_pattern,
)
from freya.topology.sustainability import LongHorizonOperationalSustainabilityEngine


def _header(label: str, title: str) -> None:
    sep = "=" * 68
    print(f"\n{sep}")
    print(f"  {label}: {title}")
    print(sep)


# ---------------------------------------------------------------------------
# EO: Recurring Retry Amplification
# ---------------------------------------------------------------------------
def scenario_eo() -> None:
    _header("EO", "Recurring Retry Amplification")
    print(
        "A retry amplification topology has been observed 3 times.\n"
        "Lifecycle classification: recurring stage.\n"
    )
    lifecycle = TopologyLifecycleManagementEngine()
    state = lifecycle.assess_lifecycle("Retry Amplification Topology", occurrence_count=3)

    pattern = OperationalTopologyPattern(
        topology_name="Retry Amplification Topology",
        recurring_partitions=["retry_pool", "governance_queue"],
        recurring_pressure_patterns=["retry_spike", "governance_congestion"],
        recurrence_frequency="occasional",
        organizational_impact="moderate",
    )

    print(render_topology_pattern(pattern))
    print()
    print(render_lifecycle_state(state))
    print(
        "\nInsight: Pattern has recurred 3 times. Preventive dampening is now feasible "
        "before this topology progresses to persistent stage."
    )


# ---------------------------------------------------------------------------
# EP: Governance Recovery Topology
# ---------------------------------------------------------------------------
def scenario_ep() -> None:
    _header("EP", "Governance Recovery Topology — Persistent Lifecycle Tracking")
    print(
        "A governance recovery bottleneck topology has been observed 6 times.\n"
        "Lifecycle classification: persistent stage.\n"
    )
    lifecycle = TopologyLifecycleManagementEngine()
    state = lifecycle.assess_lifecycle(
        "Governance Recovery Bottleneck", occurrence_count=6
    )

    pattern = OperationalTopologyPattern(
        topology_name="Governance Recovery Bottleneck",
        recurring_partitions=["governance_queue", "approval_pool"],
        recurring_pressure_patterns=["governance_congestion", "recovery_surge"],
        recurrence_frequency="frequent",
        organizational_impact="significant",
    )

    print(render_topology_pattern(pattern))
    print()
    print(render_lifecycle_state(state))
    print(
        "\nInsight: With 6 occurrences, this topology is now deeply embedded in operational "
        "behavior. Coordinated resolution across governance and approval partitions is required."
    )


# ---------------------------------------------------------------------------
# EQ: Historical Stabilization Memory
# ---------------------------------------------------------------------------
def scenario_eq() -> None:
    _header("EQ", "Historical Stabilization Memory — Influencing Next Stabilization")
    print(
        "Recalling historical memory for 'retry_amplification_after_governance_recovery'.\n"
        "The stabilization outcome was only partial — early coupling reduction was the fix.\n"
        "This memory shapes the recommendation for the current stabilization cycle.\n"
    )
    memory = OperationalTopologyMemoryEngine()
    record = memory.recall("retry_amplification_after_governance_recovery")

    if record:
        print(render_operational_memory(record))
        print(
            "\nInsight: Previous partial outcome signals that reactive coupling dampening is "
            "insufficient. Apply preventive coupling reduction proactively at governance recovery start."
        )
    else:
        print("No memory record found for this pattern key.")

    # Show all available pattern keys for reference
    print("\nKnown memory catalog keys:")
    for key in memory.known_pattern_keys():
        print(f"  - {key}")


# ---------------------------------------------------------------------------
# ER: Chronic Partition Detection
# ---------------------------------------------------------------------------
def scenario_er() -> None:
    _header("ER", "Chronic Partition Detection — Temporary Becoming Persistent")
    print(
        "A topology that began as temporary has now been observed 10 times.\n"
        "Chronic detection: is_chronic() → True.\n"
    )
    lifecycle = TopologyLifecycleManagementEngine()
    state = lifecycle.assess_lifecycle(
        "Batching Accumulation Topology", occurrence_count=10
    )

    print(render_lifecycle_state(state))
    is_chronic = lifecycle.is_chronic(state)
    print(f"\n  is_chronic()  → {is_chronic}")
    print(f"  Recurrence    → {lifecycle.recurrence_label(10)}")
    print(
        "\nInsight: What was treated as a temporary batching response has become structurally "
        "embedded in operational behavior. Root-cause structural review is now required — "
        "no further short-term interventions should be applied without governance approval."
    )


# ---------------------------------------------------------------------------
# ES: Long-Horizon Sustainability Warning
# ---------------------------------------------------------------------------
def scenario_es() -> None:
    _header("ES", "Long-Horizon Sustainability Warning — Compression Reduces Resilience")
    print(
        "Compression and batching interventions have been active for 6 cycles.\n"
        "Assessing sustainability impact at 8-cycle horizon.\n"
    )
    engine = LongHorizonOperationalSustainabilityEngine()
    result = engine.assess(
        active_topology_count=3,
        active_interventions=["compression", "batching", "smoothing"],
        horizon_cycles=8,
    )

    print(render_sustainability_summary(result))
    print(
        "\nInsight: At an 8-cycle horizon, all three active interventions cross their onset "
        "thresholds. Sustained compression degrades operational trust; batching accumulates "
        "latency; persistent smoothing delays strategic recovery. Rotation required now."
    )


# ---------------------------------------------------------------------------
# ET: Unsafe Chronic Adaptation Blocked by Governance
# ---------------------------------------------------------------------------
def scenario_et() -> None:
    _header("ET", "Unsafe Chronic Adaptation Blocked — Governance Suppression Rejected")
    print(
        "A topology pattern shows chronic recurrence of governance suppression.\n"
        "Governance rule: chronic governance suppression patterns are hard-blocked.\n"
    )
    governance = TopologyGovernanceEngine()

    bad_pattern = OperationalTopologyPattern(
        topology_name="Governance Suppression Topology",
        recurring_partitions=["review_bypass_zone", "approval_skip_path"],
        recurring_pressure_patterns=["governance_suppression", "governance_bypass"],
        recurrence_frequency="chronic",
        organizational_impact="critical",
    )

    valid, violations = governance.validate_topology(bad_pattern)
    print(f"  Topology valid  → {valid}")
    for v in violations:
        print(f"\n  {v}")

    print(
        "\nInsight: Chronic governance suppression is unconditionally blocked. "
        "Governance is not an optional layer — it applies to all topology adaptations "
        "regardless of operational pressure context."
    )


# ---------------------------------------------------------------------------
# EU: Executive Organizational Topology Summary (Full Pipeline)
# ---------------------------------------------------------------------------
def scenario_eu() -> None:
    _header("EU", "Executive Organizational Topology Summary — Full Pipeline Run")
    print(
        "Running the full OrganizationalTopologyPipeline across a mixed topology landscape:\n"
        "  - Retry Amplification Topology:       3 occurrences (recurring)\n"
        "  - Governance Recovery Bottleneck:     6 occurrences (persistent)\n"
        "  - Batching Accumulation Topology:    10 occurrences (chronic)\n"
        "Active interventions: batching, compression\n"
        "Confidence: 0.68 | Horizon: 6 cycles\n"
    )

    pipeline = OrganizationalTopologyPipeline()
    result = pipeline.run(
        topology_occurrences={
            "Retry Amplification Topology": 3,
            "Governance Recovery Bottleneck": 6,
            "Batching Accumulation Topology": 10,
        },
        active_interventions=["batching", "compression"],
        confidence=0.68,
        horizon_cycles=6,
    )

    print(result["render"])
    print(f"\n  Review Required : {result['review_required']}")
    print(f"  Evolution State : {result['evolution_state']}")
    print(
        "\nInsight: The chronic 'Batching Accumulation Topology' drives the escalating "
        "evolution state, triggers review_required=True, and surfaces active sustainability "
        "risks at the 6-cycle horizon. Governance violations are reported inline."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    scenario_eo()
    scenario_ep()
    scenario_eq()
    scenario_er()
    scenario_es()
    scenario_et()
    scenario_eu()
    print("\n" + "=" * 68)
    print("  Organizational Topology Evolution Layer — demo complete (EO–EU)")
    print("=" * 68 + "\n")
