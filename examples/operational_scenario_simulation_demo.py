"""examples/operational_scenario_simulation_demo.py

Demonstrating Freya's Operational Scenario Simulation Layer.

Seven scenarios showing bounded, governed, explainable comparison of
operational interventions — strategic coordination cognition.

Scenarios
─────────
  DF — Governance Batching Comparison
  DG — Compression vs Reservation
  DH — Recovery Impact Simulation
  DI — Coordination Stability Comparison
  DJ — Counterfactual Reasoning
  DK — Risk-Aware Recommendation (unsafe intervention blocked)
  DL — Executive Strategy Summary
"""
from __future__ import annotations

from freya.simulation import (
    OperationalSimulationPipeline,
    OperationalStrategyComparisonEngine,
    SimulationForecastingEngine,
    render_counterfactual_comparison,
    render_risk_assessment,
    render_simulation_outcome,
    render_simulation_scenario,
    render_strategy_recommendation,
)
from freya.simulation.counterfactuals import CounterfactualOperationalReasoningEngine
from freya.simulation.interventions import OperationalInterventionModelingEngine
from freya.simulation.models import OperationalScenario

# ── Shared helpers ─────────────────────────────────────────────────────────────

def _divider(label: str) -> None:
    print(f"\n{'═' * 70}")
    print(f"  {label}")
    print("═" * 70)


def _section(label: str) -> None:
    print(f"\n── {label} ──")


# ── Scenario DF — Governance Batching Comparison ──────────────────────────────

def scenario_df() -> None:
    _divider("Scenario DF — Governance Batching Comparison")
    print(
        "\nContext: Governance backlog is rising. Two options are evaluated:\n"
        "   A) Pre-batch low-priority approvals\n"
        "   B) No intervention\n"
        "Freya compares both and recommends the least-disruptive path.\n"
    )

    pipeline = OperationalSimulationPipeline()

    scenarios = [
        OperationalScenario(
            scenario_id="df-batching",
            scenario_name="Governance Batching",
            intervention_type="governance_batching",
            intervention_description="Pre-batch low-priority approvals into scheduled windows.",
            affected_workflows=["wf-travel", "wf-reporting"],
            simulation_window_minutes=15,
        ),
        OperationalScenario(
            scenario_id="df-no-action",
            scenario_name="No Intervention",
            intervention_type="no_intervention",
            intervention_description="Observe and allow natural backlog progression.",
            affected_workflows=[],
            simulation_window_minutes=15,
        ),
    ]

    result = pipeline.run(
        scenarios=scenarios,
        current_pressure=0.65,
        confidence=0.75,
        baseline_scenario_id="df-no-action",
    )

    print(result["render"])

    _section("Operational Scenario Comparison Note")
    print(
        "Scenario A — Governance Batching\n"
        "  • lower governance interruption rate\n"
        "  • moderate approval latency increase\n"
        "  • minimal operational disruption\n\n"
        "Scenario B — No Intervention\n"
        "  • escalation backlog continues to grow\n"
        "  • reactive congestion likely\n\n"
        "Recommended: Governance Batching\n"
        "Reason: Lower organizational disruption with comparable stabilization effectiveness."
    )


# ── Scenario DG — Compression vs Reservation ──────────────────────────────────

def scenario_dg() -> None:
    _divider("Scenario DG — Compression vs Reservation")
    print(
        "\nContext: Reasoning pool at 75 % utilization and rising.\n"
        "Two strategies are evaluated:\n"
        "   A) Reasoning compression for background workflows\n"
        "   B) Proactive reservation for critical workflows\n"
    )

    pipeline = OperationalSimulationPipeline()

    scenarios = [
        OperationalScenario(
            scenario_id="dg-compression",
            scenario_name="Reasoning Compression",
            intervention_type="reasoning_compression",
            intervention_description="Reduce reasoning depth for background workflows by 30 %.",
            affected_workflows=["wf-analytics", "wf-reporting"],
            simulation_window_minutes=10,
        ),
        OperationalScenario(
            scenario_id="dg-reservation",
            scenario_name="Capacity Reservation",
            intervention_type="reservation_reallocation",
            intervention_description="Reserve 25 % reasoning capacity for incident workflows.",
            affected_workflows=["wf-incident", "wf-security"],
            simulation_window_minutes=10,
        ),
    ]

    result = pipeline.run(
        scenarios=scenarios,
        current_pressure=0.72,
        confidence=0.80,
        baseline_scenario_id="dg-compression",
    )

    print(result["render"])

    if result["recommended"]:
        _section("Recommendation")
        print(f"  {result['recommended'].scenario.scenario_name}")
        for line in result["recommended"].summary():
            print(f"  {line}")


# ── Scenario DH — Recovery Impact Simulation ──────────────────────────────────

def scenario_dh() -> None:
    _divider("Scenario DH — Recovery Impact Simulation")
    print(
        "\nContext: High pressure at 0.85. Three interventions are compared\n"
        "across their recovery timelines and stabilization effectiveness.\n"
    )

    forecasting  = SimulationForecastingEngine()
    modeling     = OperationalInterventionModelingEngine()
    pressure     = 0.85

    intervention_types = ["governance_batching", "reasoning_compression", "workflow_degradation"]

    _section("Recovery Timeline Comparison")
    for itype in intervention_types:
        effect   = modeling.effect_for(itype)  # type: ignore[arg-type]
        rec_mins = forecasting.estimate_recovery_minutes(pressure, effect, window_minutes=20)
        stab_p   = forecasting.estimate_stabilization_probability(pressure, effect, 20)
        eq_desc  = forecasting.projected_equilibrium_improvement(effect, pressure)

        print(f"\n  {itype.replace('_', ' ').title()}")
        print(f"    Recovery estimate:           ~{rec_mins} minutes")
        print(f"    Stabilization probability:   {stab_p:.0%}")
        print(f"    Equilibrium:                 {eq_desc}")
        narrative = forecasting.recovery_narrative(effect, rec_mins, stab_p)
        for line in narrative:
            print(f"    {line}")


# ── Scenario DI — Coordination Stability Comparison ───────────────────────────

def scenario_di() -> None:
    _divider("Scenario DI — Coordination Stability Comparison")
    print(
        "\nContext: Moderate pressure (0.65) with multiple workflows affected.\n"
        "Four strategies evaluated for coordination stability impact.\n"
    )

    pipeline = OperationalSimulationPipeline()

    scenarios = [
        OperationalScenario(
            scenario_id="di-batching",
            scenario_name="Governance Batching",
            intervention_type="governance_batching",
            intervention_description="Batch reviews.",
            affected_workflows=["wf-travel", "wf-procurement"],
            simulation_window_minutes=20,
        ),
        OperationalScenario(
            scenario_id="di-opt-suspend",
            scenario_name="Optimization Suspension",
            intervention_type="optimization_suspension",
            intervention_description="Suspend background optimization passes.",
            affected_workflows=["wf-analytics"],
            simulation_window_minutes=20,
        ),
        OperationalScenario(
            scenario_id="di-deferral",
            scenario_name="Workflow Deferral",
            intervention_type="workflow_deferral",
            intervention_description="Defer non-critical workflows to next cycle.",
            affected_workflows=["wf-recommendations"],
            simulation_window_minutes=20,
        ),
        OperationalScenario(
            scenario_id="di-reservation",
            scenario_name="Capacity Reservation",
            intervention_type="reservation_reallocation",
            intervention_description="Reserve capacity for high-priority workflows.",
            affected_workflows=["wf-incident"],
            simulation_window_minutes=20,
        ),
    ]

    result = pipeline.run(
        scenarios=scenarios,
        current_pressure=0.65,
        confidence=0.78,
    )

    # Just show the comparison table
    if result["report"].ranked_strategies:
        table = OperationalStrategyComparisonEngine().comparison_table(
            result["report"].ranked_strategies
        )
        rec_name = result["recommended"].scenario.scenario_name if result["recommended"] else "—"
        print(render_strategy_recommendation(table, rec_name, "Highest stability improvement with lowest disruption."))


# ── Scenario DJ — Counterfactual Reasoning ────────────────────────────────────

def scenario_dj() -> None:
    _divider("Scenario DJ — Counterfactual Reasoning")
    print(
        "\nContext: Pressure at 0.78 with governance backlog growing.\n"
        "Freya reasons counterfactually: what if no action were taken?\n"
        "vs. batching, compression, or deferral.\n"
    )

    pipeline = OperationalSimulationPipeline()
    cf_engine = CounterfactualOperationalReasoningEngine()

    scenarios = [
        OperationalScenario(
            scenario_id="dj-no-action",
            scenario_name="No Intervention (Baseline)",
            intervention_type="no_intervention",
            intervention_description="No preemptive action taken.",
            affected_workflows=[],
            simulation_window_minutes=15,
        ),
        OperationalScenario(
            scenario_id="dj-batching",
            scenario_name="Governance Batching",
            intervention_type="governance_batching",
            intervention_description="Pre-batch approvals.",
            affected_workflows=["wf-travel", "wf-procurement"],
            simulation_window_minutes=15,
        ),
        OperationalScenario(
            scenario_id="dj-compression",
            scenario_name="Reasoning Compression",
            intervention_type="reasoning_compression",
            intervention_description="Compress background reasoning.",
            affected_workflows=["wf-analytics"],
            simulation_window_minutes=15,
        ),
    ]

    result = pipeline.run(
        scenarios=scenarios,
        current_pressure=0.78,
        confidence=0.72,
        baseline_scenario_id="dj-no-action",
    )

    if result["report"].counterfactual:
        print(render_counterfactual_comparison(result["report"].counterfactual))

        # Show avoided disruption
        baseline_out = result["report"].outcomes.get("dj-no-action")
        recommended_id = result["report"].counterfactual.recommended_strategy
        rec_out = result["report"].outcomes.get(recommended_id)
        if baseline_out and rec_out:
            _section("Avoided Disruption Analysis")
            avoided = cf_engine.avoided_disruption_description(baseline_out, rec_out)
            for line in avoided:
                print(f"  {line}")


# ── Scenario DK — Risk-Aware Recommendation ───────────────────────────────────

def scenario_dk() -> None:
    _divider("Scenario DK — Risk-Aware Recommendation (Unsafe Intervention Blocked)")
    print(
        "\nContext: Critical workflows are active. A workflow_degradation scenario\n"
        "is submitted for simulation. Freya's governance layer blocks it.\n"
    )

    pipeline = OperationalSimulationPipeline()

    scenarios = [
        OperationalScenario(
            scenario_id="dk-degradation",
            scenario_name="Critical Workflow Degradation",
            intervention_type="workflow_degradation",
            intervention_description="Degrade reasoning quality for all active workflows.",
            affected_workflows=["wf-incident", "wf-security", "wf-analytics"],
            simulation_window_minutes=10,
        ),
        OperationalScenario(
            scenario_id="dk-safe-opt",
            scenario_name="Optimization Suspension",
            intervention_type="optimization_suspension",
            intervention_description="Suspend background optimization — safe alternative.",
            affected_workflows=["wf-analytics"],
            simulation_window_minutes=10,
        ),
    ]

    result = pipeline.run(
        scenarios=scenarios,
        current_pressure=0.80,
        confidence=0.75,
        has_critical_workflows=True,
    )

    for scenario in result["report"].scenarios:
        sid  = scenario.scenario_id
        risk = result["report"].risk_assessments.get(sid)
        if risk:
            print(render_risk_assessment(risk))

    _section("Governance Note")
    if result["blocked"]:
        print(f"  Blocked scenarios: {', '.join(result['blocked'])}")
        print("  Critical workflow protection enforced — degradation scenario rejected.")
    if result["recommended"]:
        print(f"  Safe recommendation: {result['recommended'].scenario.scenario_name}")


# ── Scenario DL — Executive Strategy Summary ──────────────────────────────────

def scenario_dl() -> None:
    _divider("Scenario DL — Executive Strategy Summary")
    print(
        "\nContext: Full multi-strategy organizational simulation.\n"
        "Five intervention options evaluated; governed; ranked; recommended.\n"
    )

    pipeline = OperationalSimulationPipeline()

    scenarios = [
        OperationalScenario(
            scenario_id="dl-batching",
            scenario_name="Governance Batching",
            intervention_type="governance_batching",
            intervention_description="Pre-batch low-priority approvals.",
            affected_workflows=["wf-travel", "wf-procurement"],
            simulation_window_minutes=20,
        ),
        OperationalScenario(
            scenario_id="dl-compression",
            scenario_name="Reasoning Compression",
            intervention_type="reasoning_compression",
            intervention_description="Reduce reasoning depth for background workflows.",
            affected_workflows=["wf-analytics", "wf-reporting"],
            simulation_window_minutes=20,
        ),
        OperationalScenario(
            scenario_id="dl-reservation",
            scenario_name="Capacity Reservation",
            intervention_type="reservation_reallocation",
            intervention_description="Reserve capacity for incident workflows.",
            affected_workflows=["wf-incident", "wf-security"],
            simulation_window_minutes=20,
        ),
        OperationalScenario(
            scenario_id="dl-opt-suspend",
            scenario_name="Optimization Suspension",
            intervention_type="optimization_suspension",
            intervention_description="Suspend optimization passes.",
            affected_workflows=["wf-analytics"],
            simulation_window_minutes=20,
        ),
        OperationalScenario(
            scenario_id="dl-no-action",
            scenario_name="No Intervention",
            intervention_type="no_intervention",
            intervention_description="Observe and monitor.",
            affected_workflows=[],
            simulation_window_minutes=20,
        ),
    ]

    result = pipeline.run(
        scenarios=scenarios,
        current_pressure=0.70,
        confidence=0.78,
        baseline_scenario_id="dl-no-action",
    )

    print(result["render"])

    _section("Executive Summary")
    rec = result["recommended"]
    if rec:
        print(
            f"  Recommended Strategy:  {rec.scenario.scenario_name}\n"
            f"  Stability Probability: {rec.stabilization_probability:.0%}\n"
            f"  Recovery Estimate:     ~{rec.recovery_minutes} min\n"
            f"  Governance Effect:     {rec.outcome.projected_governance_effect.upper()}\n"
            f"  Reversible:            {'Yes' if rec.outcome.reversibility else 'No'}"
        )


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    print("\nFreya SDK — Operational Scenario Simulation Demo")
    print("Bounded, governed, strategic operational coordination cognition.\n")

    scenario_df()
    scenario_dg()
    scenario_dh()
    scenario_di()
    scenario_dj()
    scenario_dk()
    scenario_dl()

    print("\n" + "═" * 70)
    print("  All scenarios completed.")
    print("  Freya simulation layer: strategic · governed · explainable.")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    main()
