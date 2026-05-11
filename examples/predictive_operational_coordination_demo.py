"""examples/predictive_operational_coordination_demo.py

Demonstrating Freya's Predictive Operational Coordination Layer.

Seven scenarios that show anticipatory, governed, equilibrium-oriented
coordination — proactive stabilization before instability occurs.

Scenarios
─────────
  CY — Governance Pressure Forecast
  CZ — Reasoning Pool Forecast
  DA — Predictive Smoothing
  DB — Equilibrium Assessment
  DC — Reservation Coordination
  DD — Predictive Recovery Forecast
  DE — Predictive Coordination Summary
"""
from __future__ import annotations

from freya.predictive import (
    OperationalEquilibriumEngine,
    OperationalForecastingEngine,
    OperationalReservationEngine,
    OperationalSignalEngine,
    OperationalSmoothingEngine,
    PredictiveCoordinationPipeline,
    PredictiveGovernanceEngine,
    render_equilibrium_state,
    render_full_predictive_state,
    render_operational_forecast,
    render_predictive_adjustments,
    render_recovery_forecast,
    render_reservation_state,
)

# ── Shared helpers ─────────────────────────────────────────────────────────────

def _divider(label: str) -> None:
    print(f"\n{'═' * 70}")
    print(f"  {label}")
    print("═" * 70)


def _section(label: str) -> None:
    print(f"\n── {label} ──")


# ── Scenario CY — Governance Pressure Forecast ────────────────────────────────

def scenario_cy() -> None:
    _divider("Scenario CY — Governance Pressure Forecast")
    print(
        "\nContext: Approval latency is rising and escalation frequency has doubled.\n"
        "Freya forecasts governance congestion within 15 minutes and\n"
        "proactively pre-batches low-priority reviews.\n"
    )

    signal_engine    = OperationalSignalEngine()
    forecast_engine  = OperationalForecastingEngine()
    governance_engine = PredictiveGovernanceEngine()

    telemetry = {
        "approval_latency":     2.8,   # baseline 1.0 → 2.8×
        "escalation_frequency": 0.35,  # baseline 0.10 → 3.5×
        "retry_rate":           0.06,
    }

    signals  = signal_engine.read(telemetry)
    forecast = forecast_engine.forecast(signals, window_minutes=15)

    print(render_operational_forecast(forecast))

    gov_plan = governance_engine.assess_and_plan(
        forecast=forecast,
        pending_approvals=5,
        pending_approval_types=["expense_review", "travel_approval"],
        current_approval_latency=2.8,
    )

    if gov_plan:
        _section("Preventive Governance Actions")
        print(render_predictive_adjustments(gov_plan))

    _section("Predictive Coordination Note")
    print(
        "Governance review pressure is projected to increase within 15 minutes.\n\n"
        "Preventive Actions:\n"
        "  • Low-priority approvals pre-batched\n"
        "  • Reasoning budget reserved for incident workflows\n"
        "  • Approval bandwidth protected\n\n"
        "Expected Impact:\n"
        "  • Reduced escalation congestion\n"
        "  • Preserved incident-response governance bandwidth\n"
        "  • Smoother operational continuity"
    )


# ── Scenario CZ — Reasoning Pool Forecast ─────────────────────────────────────

def scenario_cz() -> None:
    _divider("Scenario CZ — Reasoning Pool Forecast")
    print(
        "\nContext: Reasoning pool usage has climbed to 78 % and continues rising.\n"
        "Freya forecasts exhaustion within 10 minutes and reserves capacity\n"
        "for critical incident-response workflows.\n"
    )

    pipeline = PredictiveCoordinationPipeline()

    outcome = pipeline.run(
        telemetry={
            "reasoning_pool_usage": 0.78,
            "workflow_surge_index": 1.6,
            "retry_rate":           0.09,
        },
        pending_approvals=2,
        critical_workflows=["wf-incident", "wf-security"],
        background_workflows=["wf-analytics"],
        window_minutes=10,
        current_pressure=0.68,
    )

    print(outcome["report"])

    _section("Reservation Outcome")
    for r in outcome["result"].reservations:
        print(f"  Reserved {r.reserved_capacity:.0%} of reasoning_capacity for {r.protected_for_workflow}")
        print(f"  Expires: {r.expiration_condition}")


# ── Scenario DA — Predictive Smoothing ────────────────────────────────────────

def scenario_da() -> None:
    _divider("Scenario DA — Predictive Smoothing")
    print(
        "\nContext: Multiple destabilization signals rising simultaneously.\n"
        "Freya applies a gradual reasoning taper to background workflows\n"
        "— preventing an abrupt coordination shock.\n"
    )

    signal_engine    = OperationalSignalEngine()
    forecast_engine  = OperationalForecastingEngine()
    equilibrium_eng  = OperationalEquilibriumEngine()
    smoothing_engine = OperationalSmoothingEngine()

    telemetry = {
        "reasoning_pool_usage": 0.72,
        "degradation_usage":    0.28,
        "workflow_surge_index": 1.8,
        "optimization_queue":   5.5,
        "retry_rate":           0.11,
    }

    signals     = signal_engine.read(telemetry)
    forecast    = forecast_engine.forecast(signals, window_minutes=20)
    equilibrium = equilibrium_eng.assess(signals, forecast=forecast)

    print(render_equilibrium_state(equilibrium))

    smooth_plan = smoothing_engine.plan(
        equilibrium=equilibrium,
        forecast=forecast,
        affected_workflows=["wf-analytics", "wf-reporting", "wf-recommendations"],
    )

    if smooth_plan:
        _section("Smoothing Plan")
        print(render_predictive_adjustments(smooth_plan))
        print(f"\n  Phase description: {smoothing_engine.describe_phase(smooth_plan.smoothing_phase)}")

    _section("Outcome")
    print(
        "Reasoning depth gradually reduced for background workflows.\n"
        "No abrupt operational shock — transition is smooth and bounded.\n"
        "Full capacity restored automatically when pressure normalises."
    )


# ── Scenario DB — Equilibrium Assessment ──────────────────────────────────────

def scenario_db() -> None:
    _divider("Scenario DB — Equilibrium Assessment")
    print(
        "\nContext: Mixed signal environment — some improving, some deteriorating.\n"
        "Freya assesses the overall organizational equilibrium state\n"
        "and determines whether proactive stabilization is warranted.\n"
    )

    signal_engine   = OperationalSignalEngine()
    forecast_engine = OperationalForecastingEngine()
    equilibrium_eng = OperationalEquilibriumEngine()

    # Scenario: governance improving but reasoning still rising
    telemetry = {
        "approval_latency":     1.2,   # slightly above baseline
        "escalation_frequency": 0.08,  # below baseline — improving
        "reasoning_pool_usage": 0.68,  # rising
        "retry_rate":           0.07,  # creeping up
        "degradation_usage":    0.15,  # some degradation present
    }

    signals     = signal_engine.read(telemetry)
    forecast    = forecast_engine.forecast(signals, window_minutes=20)
    equilibrium = equilibrium_eng.assess(signals, forecast=forecast)

    _section("Signal Overview")
    for line in signal_engine.describe(signals):
        print(f"  {line}")

    _section("Equilibrium State")
    print(render_equilibrium_state(equilibrium))

    _section("Stabilization Decision")
    if equilibrium.stabilization_recommended:
        print("Proactive stabilization recommended based on current trend analysis.")
    else:
        print("System within acceptable equilibrium bounds — continue monitoring.")


# ── Scenario DC — Reservation Coordination ────────────────────────────────────

def scenario_dc() -> None:
    _divider("Scenario DC — Reservation Coordination")
    print(
        "\nContext: Incident surge is forecast with high confidence.\n"
        "Freya proactively reserves reasoning capacity for incident-response\n"
        "workflows before demand peaks.\n"
    )

    signal_engine     = OperationalSignalEngine()
    forecast_engine   = OperationalForecastingEngine()
    reservation_engine = OperationalReservationEngine()

    telemetry = {
        "workflow_surge_index": 2.2,   # 2.2× baseline incidents
        "reasoning_pool_usage": 0.65,
        "retry_rate":           0.10,
    }

    signals     = signal_engine.read(telemetry)
    forecast    = forecast_engine.forecast(signals, window_minutes=10)

    print(render_operational_forecast(forecast))

    critical_wfs = ["wf-incident-alpha", "wf-incident-beta", "wf-security"]
    reservations = []

    for wf in critical_wfs:
        r = reservation_engine.reserve(
            resource="reasoning_capacity",
            protected_workflow=wf,
            reason="Incident surge forecast — proactive capacity protection.",
            forecast=forecast,
            base_fraction=0.20,
        )
        if r:
            reservations.append(r)

    _section("Active Reservations")
    print(render_reservation_state(reservations))

    total_reserved = reservation_engine.total_reserved("reasoning_capacity")
    available      = reservation_engine.available_capacity("reasoning_capacity")
    print(f"\n  Total reserved:  {total_reserved:.0%}")
    print(f"  Available:       {available:.0%}")


# ── Scenario DD — Predictive Recovery Forecast ────────────────────────────────

def scenario_dd() -> None:
    _divider("Scenario DD — Predictive Recovery Forecast")
    print(
        "\nContext: Pressure has peaked and signals are beginning to stabilise.\n"
        "Freya forecasts the recovery timeline and plans reservation release.\n"
    )

    signal_engine   = OperationalSignalEngine()
    forecast_engine = OperationalForecastingEngine()

    # Post-peak telemetry — values returning toward baseline
    telemetry = {
        "reasoning_pool_usage": 0.58,  # was 0.78, now declining
        "workflow_surge_index": 1.3,   # falling
        "approval_latency":     1.4,   # falling toward baseline
        "retry_rate":           0.07,  # normalising
    }

    signals  = signal_engine.read(telemetry)
    forecast = forecast_engine.forecast(signals, window_minutes=15)
    recovery = forecast_engine.recovery_forecast(
        current_pressure=0.45,
        active_signal_count=len(signal_engine.rising_signals(signals)),
        trend="improving",
    )

    print(render_operational_forecast(forecast))

    _section("Recovery Forecast")
    print(render_recovery_forecast(recovery))

    _section("Post-Recovery Plan")
    print(
        "As pressure normalises:\n"
        "  • Reasoning capacity reservations will be released\n"
        "  • Smoothing phases stepped back gradually\n"
        "  • Background workflows restored to full depth\n"
        "  • Governance batching dissolved when backlog clears"
    )


# ── Scenario DE — Predictive Coordination Summary ─────────────────────────────

def scenario_de() -> None:
    _divider("Scenario DE — Predictive Coordination Summary")
    print(
        "\nContext: Full organizational predictive coordination snapshot.\n"
        "Mixed pressure environment with 4 active signals.\n"
        "Freya renders a complete anticipatory coordination report.\n"
    )

    pipeline = PredictiveCoordinationPipeline()

    outcome = pipeline.run(
        telemetry={
            "approval_latency":     2.0,
            "escalation_frequency": 0.22,
            "reasoning_pool_usage": 0.70,
            "retry_rate":           0.09,
            "degradation_usage":    0.18,
            "workflow_surge_index": 1.5,
        },
        pending_approvals=4,
        critical_workflows=["wf-incident", "wf-security"],
        background_workflows=["wf-analytics", "wf-reporting", "wf-recommendations"],
        window_minutes=15,
        current_pressure=0.65,
        stability_trend="stable",
    )

    print(outcome["report"])

    _section("Coordination Ledger")
    print(f"  Action warranted:              {'Yes' if outcome['action_warranted'] else 'No'}")
    print(f"  Stabilization recommended:     {'Yes' if outcome['stabilization_recommended'] else 'No'}")
    summary = pipeline.reservation_summary()
    print(f"  Active reservations:           {summary.get('active', 0)}")
    print(f"  Adjustment plans:              {len(outcome['result'].adjustment_plans)}")

    _section("Anticipatory Coordination Summary")
    print(
        "The predictive layer has coordinated proactively across all active workflows.\n"
        "No operational shock has occurred — transitions are gradual and bounded.\n"
        "Governance reviews remain on track.\n"
        "All reservations and smoothing adjustments are reversible."
    )


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    print("\nFreya SDK — Predictive Operational Coordination Demo")
    print("Anticipatory, governed, equilibrium-oriented workflow coordination.\n")

    scenario_cy()
    scenario_cz()
    scenario_da()
    scenario_db()
    scenario_dc()
    scenario_dd()
    scenario_de()

    print("\n" + "═" * 70)
    print("  All scenarios completed.")
    print("  Freya predictive layer: anticipatory · adaptive · governed.")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    main()
