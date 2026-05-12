"""examples/causal_operational_reasoning_demo.py

Causal Operational Reasoning Layer — Scenarios DM through DS.

Each scenario is self-contained and exercises a distinct aspect of the
freya.causal module. No external services required.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running from the repo root without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent))

from freya.causal import (
    CausalGovernanceEngine,
    CausalInterventionAnalysisEngine,
    CausalReasoningPipeline,
    CausalStabilityEngine,
    OperationalCausalChainEngine,
    OperationalPropagationEngine,
    render_cascade_analysis,
    render_causal_chain,
    render_intervention_causality,
    render_stabilization_propagation,
)


def divider(label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}\n")


# ---------------------------------------------------------------------------
# Scenario DM — Governance Retry Cascade
# ---------------------------------------------------------------------------
def scenario_dm() -> None:
    divider("Scenario DM — Governance Retry Cascade")

    engine = OperationalCausalChainEngine()
    chain = engine.build("governance_congestion")

    print("Root event: governance_congestion")
    print(f"Propagation strength: {chain.propagation_strength}")
    print(f"Confidence: {chain.confidence_score:.0%}")
    print()
    print(render_causal_chain(chain))

    # Show how retry_spike compounds the risk.
    retry_chain = engine.build("retry_spike")
    print()
    print("Compounding event: retry_spike")
    print()
    print(render_causal_chain(retry_chain))

    print(
        "\nInsight: When governance congestion co-occurs with a retry spike,\n"
        "         both chains are amplifying. Combined, they may escalate into\n"
        "         a full destabilization cascade (see Scenario DQ).\n"
    )


# ---------------------------------------------------------------------------
# Scenario DN — Stabilization Propagation
# ---------------------------------------------------------------------------
def scenario_dn() -> None:
    divider("Scenario DN — Stabilization Propagation (Equilibrium Reinforcement)")

    stability = CausalStabilityEngine()

    batching_prop = stability.analyze("batching_applied", current_pressure=0.65)
    smoothing_prop = stability.analyze("smoothing_applied", current_pressure=0.65)

    print("Individual stabilization effects at pressure 0.65:\n")
    print(render_stabilization_propagation(batching_prop))
    print()
    print(render_stabilization_propagation(smoothing_prop))

    combined = stability.combined_stability(
        interventions=["batching_applied", "smoothing_applied"],
        current_pressure=0.65,
    )
    print(f"\nCombined stabilization effect:  {combined!r}")
    print(
        "\nInsight: Two complementary interventions generate a reinforcement\n"
        "         chain whose combined effect exceeds either individually.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DO — Compression Side Effects
# ---------------------------------------------------------------------------
def scenario_do() -> None:
    divider("Scenario DO — Compression Side Effects (reasoning_compression)")

    interventions = CausalInterventionAnalysisEngine()
    impact = interventions.analyze("reasoning_compression")

    print(render_intervention_causality(impact))
    print()
    print("Key insight — unintended consequences:")
    for c in impact.unintended_consequences:
        print(f"  ! {c}")
    print(
        "\nInsight: reasoning_compression trades analysis depth for throughput.\n"
        "         The reduction in cognitive load reduces latency, but shallower\n"
        "         analysis produces more reprocessing requests — partially\n"
        "         negating the stability gain. Net delta is +0.20, not the +0.35\n"
        "         of governance_batching.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DP — Reservation Recovery Chain
# ---------------------------------------------------------------------------
def scenario_dp() -> None:
    divider("Scenario DP — Reservation Recovery Chain")

    chains = OperationalCausalChainEngine()
    stability = CausalStabilityEngine()

    chain = chains.build("reservation_applied")
    print("Causal chain — reservation_applied:\n")
    print(render_causal_chain(chain))

    prop = stability.analyze("reservation_applied", current_pressure=0.55)
    print()
    print("Stabilization propagation:\n")
    print(render_stabilization_propagation(prop))

    print(
        "\nInsight: Reserved capacity provides a buffer that decouples competing\n"
        "         workflows. The dampening effect propagates through lower retry\n"
        "         rates, improved SLA compliance, and reduced governance load.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DQ — Destabilization Cascade Detection
# ---------------------------------------------------------------------------
def scenario_dq() -> None:
    divider("Scenario DQ — Destabilization Cascade Detection")

    propagation = OperationalPropagationEngine()

    active_events = ["governance_congestion", "retry_spike"]
    pressure = 0.80
    workflow_count = 12

    print(f"Active events:   {active_events}")
    print(f"System pressure: {pressure:.0%}")
    print(f"Workflow count:  {workflow_count}")
    print()

    cascade = propagation.detect_cascade(
        active_event_types=active_events,
        current_pressure=pressure,
        affected_workflow_count=workflow_count,
    )

    if cascade is None:
        print("No cascade detected — system within tolerable bounds.")
    else:
        print(render_cascade_analysis(cascade))
        print(
            f"\nCascade detected: is_amplifying={cascade.is_amplifying}, "
            f"depth={cascade.cascade_depth}, risk={cascade.equilibrium_risk!r}\n"
        )

    print(
        "Insight: A 0.80 pressure reading with both governance_congestion and\n"
        "         retry_spike active exceeds the 0.60 threshold for cascade\n"
        "         detection. The amplification pair triggers a feedback loop.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DR — Mitigation Recommendation
# ---------------------------------------------------------------------------
def scenario_dr() -> None:
    divider("Scenario DR — Mitigation Recommendation (Governance Validation)")

    propagation = OperationalPropagationEngine()
    governance = CausalGovernanceEngine()
    interventions = CausalInterventionAnalysisEngine()

    cascade = propagation.detect_cascade(
        active_event_types=["degradation_onset", "retry_spike"],
        current_pressure=0.75,
        affected_workflow_count=9,
    )

    if cascade is not None:
        print("Cascade found:\n")
        print(render_cascade_analysis(cascade))

        valid, violations = governance.validate_cascade(cascade)
        needs_review = governance.review_required(cascade, confidence=0.82)

        print(f"\nGovernance valid: {valid}")
        if violations:
            print("Violations:")
            for v in violations:
                print(f"  ⚠  {v}")
        print(f"Human review required: {needs_review}")

    # Surface a safe bounded recommendation.
    print("\nEvaluating bounded intervention (governance_batching):\n")
    impact = interventions.analyze("governance_batching")
    print(render_intervention_causality(impact))
    print(
        "\nInsight: governance_batching carries no unsafe unintended consequences\n"
        "         and delivers a +0.35 net stability delta — the recommended\n"
        "         first-response intervention when a cascade is detected.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DS — Executive Causal Summary (Full Pipeline)
# ---------------------------------------------------------------------------
def scenario_ds() -> None:
    divider("Scenario DS — Executive Causal Summary (Full Pipeline Run)")

    pipeline = CausalReasoningPipeline()

    result = pipeline.run(
        active_event_types=["governance_congestion", "retry_spike", "degradation_onset"],
        interventions_applied=["batching_applied", "reservation_applied"],
        pressure=0.78,
        confidence=0.80,
    )

    report = result["report"]

    print(f"Cascade detected:   {result['cascade_detected']}")
    print(f"Review required:    {result['review_required']}")
    print(f"Overall stability:  {report.overall_stability_delta:+.0%}")
    print(f"Is stabilizing:     {report.is_stabilizing}")
    print()
    print(result["render"])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    print("\nFreya SDK — Causal Operational Reasoning Demo (Scenarios DM–DS)")
    print("=" * 72)

    scenario_dm()
    scenario_dn()
    scenario_do()
    scenario_dp()
    scenario_dq()
    scenario_dr()
    scenario_ds()

    print("\nAll causal scenarios completed successfully.\n")


if __name__ == "__main__":
    main()
