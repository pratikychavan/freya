"""examples/coordination_sequencing_demo.py

Coordination Sequencing + Adaptive Intervention Layer — Scenarios DT through DZ.

Each scenario is self-contained and exercises a distinct aspect of the
freya.sequencing module. No external services required.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from freya.sequencing import (
    AdaptiveInterventionEngine,
    CoordinationSequencingPipeline,
    EquilibriumTransitionEngine,
    InterventionSequence,
    OperationalPhaseManagementEngine,
    OperationalRecoveryCoordinationEngine,
    SequencingGovernanceEngine,
    render_adaptive_decision,
    render_coordination_sequence,
    render_phase_transition,
    render_recovery_progression,
)


def divider(label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}\n")


# ---------------------------------------------------------------------------
# Scenario DT — Sequenced Stabilization (batching before compression)
# ---------------------------------------------------------------------------
def scenario_dt() -> None:
    divider("Scenario DT — Sequenced Stabilization")

    pipeline = CoordinationSequencingPipeline()
    result = pipeline.run(
        active_event_types=["governance_congestion", "retry_spike"],
        active_interventions=["batching_applied"],
        pressure=0.68,
        pressure_trend="stable",
        confidence=0.75,
    )

    report = result["report"]
    print(f"Selected sequence: {report.recommended_sequence.sequence_name}")
    print(f"Phase order:       {' → '.join(report.recommended_sequence.phases)}")
    print()
    print(render_coordination_sequence(report.recommended_sequence))

    print(
        "\nInsight: Governance batching is applied first to reduce interruption churn.\n"
        "         Compression is not recommended until batching is confirmed effective.\n"
        "         Sequence intelligence prevents premature escalation.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DU — Adaptive Escalation (compression avoided after improvement)
# ---------------------------------------------------------------------------
def scenario_du() -> None:
    divider("Scenario DU — Adaptive Escalation (Compression Avoided)")

    engine = AdaptiveInterventionEngine()

    # Pressure improving with batching active — compression should be deferred.
    decision = engine.recommend(
        current_phase="retry_stabilization",
        current_pressure=0.55,
        active_interventions=["batching_applied"],
        pressure_trend="improving",
    )

    print("Context: retry_stabilization phase, batching active, pressure improving")
    print()
    print(render_adaptive_decision(decision))

    print(
        "\nInsight: The adaptive engine defers compression because batching is already\n"
        "         producing stabilization. Over-intervention would risk equilibrium\n"
        "         disruption without additional gain.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DV — Progressive Recovery (reasoning depth restored gradually)
# ---------------------------------------------------------------------------
def scenario_dv() -> None:
    divider("Scenario DV — Progressive Recovery")

    engine = OperationalRecoveryCoordinationEngine()

    # Three pressure snapshots showing recovery progression.
    snapshots = [
        (0.72, "stable",    "Early-stage — pressure high, mitigation active"),
        (0.42, "improving", "Mid-stage — pressure falling, conservative restoration begins"),
        (0.22, "improving", "Late-stage — near-full restoration in progress"),
    ]
    for pressure, trend, label in snapshots:
        prog = engine.assess_recovery(
            current_pressure=pressure,
            active_interventions=["batching_applied"],
            pressure_trend=trend,
        )
        print(f"--- {label} (pressure={pressure:.0%}, trend={trend}) ---")
        print(render_recovery_progression(prog))
        print()

    print(
        "Insight: Recovery is staged across pressure thresholds. Reasoning depth\n"
        "         partially restores at 0.42 and fully restores only below 0.30.\n"
        "         Each increment is validated before the next is released.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DW — Equilibrium-Aware Restoration (pacing slowed)
# ---------------------------------------------------------------------------
def scenario_dw() -> None:
    divider("Scenario DW — Equilibrium-Aware Restoration (Pacing Adjusted)")

    eq = EquilibriumTransitionEngine()

    # Case 1: transition attempted too early — pressure still 0.52
    assessment_early = eq.assess_transition(
        from_phase="contention_reduction",
        to_phase="restoration",
        current_pressure=0.52,
        recent_pressure_delta=-0.06,
    )
    print("Attempt: contention_reduction → restoration at pressure 0.52")
    print(render_phase_transition("contention_reduction", "restoration", assessment_early))

    # Case 2: same transition at safe pressure
    assessment_safe = eq.assess_transition(
        from_phase="contention_reduction",
        to_phase="restoration",
        current_pressure=0.38,
        recent_pressure_delta=-0.04,
    )
    print("\nAttempt: contention_reduction → restoration at pressure 0.38")
    print(render_phase_transition("contention_reduction", "restoration", assessment_safe))

    print(
        "\nInsight: At 0.52, the engine slows pacing — restoration would be premature.\n"
        "         At 0.38, pressure ceiling is satisfied and pacing is approved.\n"
        "         Equilibrium awareness prevents rebound destabilization.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DX — Dynamic Intervention Ordering (reservation deferred)
# ---------------------------------------------------------------------------
def scenario_dx() -> None:
    divider("Scenario DX — Dynamic Intervention Ordering (Reservation Deferred)")

    engine = AdaptiveInterventionEngine()

    # smoothing active + trend improving → reservation should be deferred
    decision = engine.recommend(
        current_phase="contention_reduction",
        current_pressure=0.50,
        active_interventions=["smoothing_applied"],
        pressure_trend="improving",
    )

    print("Context: contention_reduction phase, smoothing active, pressure improving")
    print()
    print(render_adaptive_decision(decision))

    # Now pressure worsening — reservation becomes warranted
    decision_escalated = engine.recommend(
        current_phase="contention_reduction",
        current_pressure=0.62,
        active_interventions=["smoothing_applied"],
        pressure_trend="worsening",
    )

    print("\nContext: same phase, pressure worsening to 0.62")
    print()
    print(render_adaptive_decision(decision_escalated))

    print(
        "\nInsight: Reservation is deferred when smoothing is working. It is applied\n"
        "         only when pressure worsens beyond the safe threshold. Dynamic\n"
        "         ordering avoids premature resource over-commitment.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DY — Unsafe Sequence Blocked
# ---------------------------------------------------------------------------
def scenario_dy() -> None:
    divider("Scenario DY — Unsafe Sequence Blocked")

    governance = SequencingGovernanceEngine()

    # Sequence that skips contention_reduction before restoration — unsafe
    unsafe_sequence = InterventionSequence(
        sequence_name="skip_to_restoration",
        phases=["Retry Stabilization", "Operational Restoration"],
        expected_stabilization_effect="Rapid restoration without contention management.",
        projected_recovery_profile="Aggressive — skips contention phase entirely.",
        confidence_score=0.72,
    )

    valid, violations = governance.validate_sequence(unsafe_sequence)
    print(f"Sequence: {unsafe_sequence.sequence_name}")
    print(f"Governance valid: {valid}")
    if violations:
        print("Violations:")
        for v in violations:
            print(f"  ⚠  {v}")

    # Transition blocked — restoration when pressure still 0.58
    trans_valid, trans_violations = governance.validate_transition(
        from_phase="retry_stabilization",
        to_phase="restoration",
        current_pressure=0.58,
    )
    print(f"\nTransition retry_stabilization → restoration at 0.58:")
    print(f"  Allowed: {trans_valid}")
    for v in trans_violations:
        print(f"  ⚠  {v}")

    print(
        "\nInsight: The governance engine blocks sequences that attempt restoration\n"
        "         before pressure is reduced below 0.50 or skip prerequisite phases.\n"
        "         All sequencing must remain bounded and explainable.\n"
    )


# ---------------------------------------------------------------------------
# Scenario DZ — Executive Coordination Summary (Full Pipeline)
# ---------------------------------------------------------------------------
def scenario_dz() -> None:
    divider("Scenario DZ — Executive Coordination Summary (Full Pipeline Run)")

    pipeline = CoordinationSequencingPipeline()

    result = pipeline.run(
        active_event_types=["governance_congestion", "retry_spike", "degradation_onset"],
        active_interventions=["batching_applied", "smoothing_applied"],
        pressure=0.65,
        pressure_trend="improving",
        confidence=0.78,
    )

    report = result["report"]
    print(f"Sequence selected:  {report.recommended_sequence.sequence_name}")
    print(f"Current phase:      {report.current_phase_name}")
    print(f"Review required:    {result['review_required']}")
    print(f"Governance safe:    {result['is_safe']}")
    if report.governance_violations:
        print("Governance notes:")
        for v in report.governance_violations:
            print(f"  ⚠  {v}")
    print()
    print(result["render"])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    print("\nFreya SDK — Coordination Sequencing + Adaptive Intervention Demo (DT–DZ)")
    print("=" * 72)

    scenario_dt()
    scenario_du()
    scenario_dv()
    scenario_dw()
    scenario_dx()
    scenario_dy()
    scenario_dz()

    print("\nAll coordination sequencing scenarios completed successfully.\n")


if __name__ == "__main__":
    main()
