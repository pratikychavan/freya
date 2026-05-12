"""examples/multi_equilibrium_demo.py

Multi-Equilibrium Operational Cognition Layer — Scenarios EA through EG.

Each scenario is self-contained and exercises a distinct aspect of the
freya.equilibrium module. No external services required.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from freya.equilibrium import (
    AsynchronousRecoveryCoordinationEngine,
    CrossZonePropagationEngine,
    EquilibriumGovernanceEngine,
    MultiEquilibriumPipeline,
    OperationalEquilibriumBalancingEngine,
    OperationalZoneManagementEngine,
    ZoneRecoveryPlan,
    render_cross_zone_propagation,
    render_multi_equilibrium_summary,
    render_recovery_plan,
    render_zone_state,
)
from freya.equilibrium.models import MultiEquilibriumAssessment


def divider(label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}\n")


# ---------------------------------------------------------------------------
# Scenario EA — Governance Zone Recovery
# ---------------------------------------------------------------------------
def scenario_ea() -> None:
    divider("Scenario EA — Governance Zone Recovery (Independent)")

    zone_mgr = OperationalZoneManagementEngine()
    recovery = AsynchronousRecoveryCoordinationEngine()

    # Governance recovering independently; other zones at near-normal pressure.
    governance_zone = zone_mgr.build_zone("governance", pressure_override=0.38)
    print(f"Governance Zone state: {governance_zone.equilibrium_state}")
    print(f"Pressure: {governance_zone.pressure_level:.0%}")
    print()
    print(render_zone_state(governance_zone))

    plan = recovery.plan_for_zone("governance", governance_zone)
    print()
    print(render_recovery_plan(plan))

    print(
        "\nInsight: Governance zone recovers independently at its own pacing.\n"
        "         Other zones are not affected — no global restoration is triggered.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EB — Reasoning Zone Instability After Governance Recovery
# ---------------------------------------------------------------------------
def scenario_eb() -> None:
    divider("Scenario EB — Reasoning Zone Instability After Governance Recovery")

    zone_mgr = OperationalZoneManagementEngine()

    # Governance now recovered; reasoning still high pressure.
    gov = zone_mgr.build_zone("governance", pressure_override=0.28)
    rsn = zone_mgr.build_zone("reasoning", pressure_override=0.72)

    print("Governance Zone (recovered):  ", gov.equilibrium_state)
    print("Reasoning Zone  (unstable):   ", rsn.equilibrium_state)
    print()
    print(render_zone_state(gov))
    print()
    print(render_zone_state(rsn))

    recovery = AsynchronousRecoveryCoordinationEngine()
    rsn_plan = recovery.plan_for_zone("reasoning", rsn)
    print()
    print(render_recovery_plan(rsn_plan))

    print(
        "\nInsight: Zones stabilize independently. Governance recovery does NOT\n"
        "         automatically restore reasoning — reasoning has its own trajectory.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EC — Cross-Zone Propagation (optimization recovery → reasoning pressure)
# ---------------------------------------------------------------------------
def scenario_ec() -> None:
    divider("Scenario EC — Cross-Zone Propagation (Optimization → Reasoning)")

    zone_mgr = OperationalZoneManagementEngine()
    propagation = CrossZonePropagationEngine()

    zones = zone_mgr.build_all_zones(
        pressure_map={
            "governance":   0.30,
            "reasoning":    0.60,   # borderline
            "optimization": 0.72,   # high — destabilizing neighbour
            "delegation":   0.35,
            "coordination": 0.50,
            "recovery":     0.40,
        }
    )

    effects = propagation.detect_effects(zones)
    print(f"Active propagation effects detected: {len(effects)}")
    print()
    print(render_cross_zone_propagation(effects))

    high = propagation.highest_severity_effects(effects)
    if high:
        print(f"\nHigh-severity effects ({len(high)}):")
        for e in high:
            print(f"  ▲▲ {e.source_zone} → {e.target_zone}: {e.propagation_effect}")

    print(
        "\nInsight: High optimization pressure propagates into the reasoning zone,\n"
        "         increasing contention. Recovery ordering must account for this.\n"
    )


# ---------------------------------------------------------------------------
# Scenario ED — Asymmetric Recovery (zones restored at different rates)
# ---------------------------------------------------------------------------
def scenario_ed() -> None:
    divider("Scenario ED — Asymmetric Recovery (Staggered Zone Restoration)")

    zone_mgr = OperationalZoneManagementEngine()
    recovery = AsynchronousRecoveryCoordinationEngine()

    zones = zone_mgr.build_all_zones(
        pressure_map={
            "governance":   0.25,   # nearly restored
            "reasoning":    0.58,   # still recovering
            "optimization": 0.70,   # unstable
            "delegation":   0.32,   # stabilized
            "coordination": 0.45,   # recovering
            "recovery":     0.35,   # stabilized
        }
    )

    order = recovery.recovery_order(zones)
    print("Recommended recovery order (most urgent first):")
    for i, key in enumerate(order, start=1):
        z = zones[key]
        print(f"  {i}. {z.zone_name:<22} pressure={z.pressure_level:.0%}  state={z.equilibrium_state}")

    print()
    # Show staggered plans for top 3 zones.
    for key in order[:3]:
        plan = recovery.plan_for_zone(key, zones[key])
        print(render_recovery_plan(plan))
        print()

    print(
        "Insight: Each zone recovers at its own pace anchored to its own pressure.\n"
        "         Optimization is deferred while reasoning and governance need attention.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EE — Unsafe Synchronized Recovery Blocked
# ---------------------------------------------------------------------------
def scenario_ee() -> None:
    divider("Scenario EE — Unsafe Synchronized Recovery Blocked")

    zone_mgr = OperationalZoneManagementEngine()
    governance = EquilibriumGovernanceEngine()

    zones = zone_mgr.build_all_zones(
        pressure_map={
            "governance":   0.75,
            "reasoning":    0.78,
            "optimization": 0.72,
            "delegation":   0.68,
        }
    )

    # Attempt to recover all unstable zones in alphabetical order (unsafe).
    unsafe_order = ["delegation", "governance", "optimization", "reasoning"]
    valid, violations = governance.validate_recovery_order(unsafe_order, zones)
    print(f"Proposed order: {' → '.join(unsafe_order)}")
    print(f"Governance valid: {valid}")
    if violations:
        print("Violations:")
        for v in violations:
            print(f"  ⚠  {v}")

    # Propose the governance-safe ordering instead.
    from freya.equilibrium.recovery import AsynchronousRecoveryCoordinationEngine
    rec = AsynchronousRecoveryCoordinationEngine()
    safe_order = rec.recovery_order(zones)
    valid2, violations2 = governance.validate_recovery_order(safe_order, zones)
    print(f"\nGovernance-derived safe order: {' → '.join(safe_order)}")
    print(f"Governance valid: {valid2}")
    if violations2:
        for v in violations2:
            print(f"  ⚠  {v}")
    else:
        print("  ✓ All recovery ordering constraints satisfied.")

    print(
        "\nInsight: Simultaneous recovery of 4 unstable zones is blocked by governance.\n"
        "         The engine derives a staggered order that respects prerequisites.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EF — Equilibrium Balancing
# ---------------------------------------------------------------------------
def scenario_ef() -> None:
    divider("Scenario EF — Equilibrium Balancing (Stabilization Redistribution)")

    zone_mgr = OperationalZoneManagementEngine()
    balancer = OperationalEquilibriumBalancingEngine()

    zones = zone_mgr.build_all_zones(
        pressure_map={
            "governance":   0.68,   # high — should block delegation
            "reasoning":    0.64,   # high — should pause optimization
            "optimization": 0.50,
            "delegation":   0.40,
            "coordination": 0.45,
            "recovery":     0.35,
        }
    )

    recommendations = balancer.balance(zones)
    print(f"Balancing recommendations generated: {len(recommendations)}")
    for rec in recommendations:
        print(f"\n  Rule:    {rec['rule_name']}")
        print(f"  Zone:    {rec['affected_zone']}")
        print(f"  Action:  {rec['balancing_action']}")

    # Check specific pause gates.
    pause_opt, reason_opt = balancer.should_pause_zone_restoration("optimization", zones)
    pause_del, reason_del = balancer.should_pause_zone_restoration("delegation", zones)
    print(f"\nPause optimization restoration? {pause_opt}")
    print(f"  Reason: {reason_opt}")
    print(f"Pause delegation restoration?   {pause_del}")
    print(f"  Reason: {reason_del}")

    print(
        "\nInsight: Balancing redistributes effort — optimization deferred while reasoning\n"
        "         is unstable, delegation deferred while governance needs attention.\n"
        "         Zones restored strategically, NOT globally.\n"
    )


# ---------------------------------------------------------------------------
# Scenario EG — Executive Multi-Equilibrium Summary (Full Pipeline)
# ---------------------------------------------------------------------------
def scenario_eg() -> None:
    divider("Scenario EG — Executive Multi-Equilibrium Summary (Full Pipeline)")

    pipeline = MultiEquilibriumPipeline()

    result = pipeline.run(
        pressure_map={
            "governance":   0.38,   # recovering
            "reasoning":    0.68,   # unstable
            "optimization": 0.58,   # recovering
            "delegation":   0.32,   # stabilized
            "coordination": 0.50,   # recovering
            "recovery":     0.28,   # stabilized
        },
        confidence=0.76,
    )

    report = result["report"]
    print(f"Global stability:   {result['global_stability']}")
    print(f"Review required:    {result['review_required']}")
    if report.assessment:
        print(f"Unstable zones:     {report.assessment.unstable_zones}")
        print(f"Recovering zones:   {report.assessment.recovering_zones}")
        print(f"Stabilized zones:   {report.assessment.stabilized_zones}")
    print()
    print(result["render"])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    print("\nFreya SDK — Multi-Equilibrium Operational Cognition Demo (EA–EG)")
    print("=" * 72)

    scenario_ea()
    scenario_eb()
    scenario_ec()
    scenario_ed()
    scenario_ee()
    scenario_ef()
    scenario_eg()

    print("\nAll multi-equilibrium scenarios completed successfully.\n")


if __name__ == "__main__":
    main()
