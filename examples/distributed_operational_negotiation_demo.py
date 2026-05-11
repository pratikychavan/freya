"""examples/distributed_operational_negotiation_demo.py

Demonstrating Freya's Distributed Operational Negotiation Layer.

Seven scenarios that show collaborative, governed coordination across
multiple concurrent workflows — adaptive, bounded, and always reversible.

Scenarios
─────────
  CR — Graceful Workflow Degradation
  CS — Elastic Resource Borrowing
  CT — Optimization Deferral
  CU — Governance Batching
  CV — Negotiated Multi-Workflow Coordination
  CW — Recovery + Reversal
  CX — Organizational Negotiation Summary
"""
from __future__ import annotations

from freya.negotiation import (
    DistributedNegotiationPipeline,
    GracefulOperationalDegradationEngine,
    OperationalNegotiationContractEngine,
    render_degradation_plan,
    render_full_negotiation_state,
    render_negotiation_contract,
    render_negotiation_summary,
    render_resource_adjustment,
)
from freya.negotiation.elasticity import ElasticOperationalResourceEngine
from freya.negotiation.engine import WorkflowSnapshot

# ── Shared helpers ─────────────────────────────────────────────────────────────

def _divider(label: str) -> None:
    print(f"\n{'═' * 70}")
    print(f"  {label}")
    print("═" * 70)


def _section(label: str) -> None:
    print(f"\n── {label} ──")


# ── Scenario CR — Graceful Workflow Degradation ────────────────────────────────

def scenario_cr() -> None:
    _divider("Scenario CR — Graceful Workflow Degradation")
    print(
        "\nContext: wf-incident (critical) is under extreme resource pressure.\n"
        "wf-reporting (low priority) voluntarily reduces its reasoning depth\n"
        "so that incident-response workflows can maintain full capacity.\n"
    )

    degradation_engine = GracefulOperationalDegradationEngine()

    plan = degradation_engine.plan(
        workflow_id="wf-reporting",
        criticality="low",
        current_pressure=0.88,
        current_quality=1.0,
    )

    print(render_degradation_plan(plan))

    _section("Operational Coordination Note")
    print(
        "wf-reporting temporarily reduced reasoning depth\n"
        "to preserve execution capacity for incident-response workflows.\n\n"
        "Expected Impact:\n"
        "  • reporting quality slightly reduced\n"
        "  • incident-response latency improved\n"
        "  • governance guarantees preserved\n\n"
        "Reversibility:\n"
        "  Automatic recovery after resource pressure normalizes."
    )


# ── Scenario CS — Elastic Resource Borrowing ──────────────────────────────────

def scenario_cs() -> None:
    _divider("Scenario CS — Elastic Resource Borrowing")
    print(
        "\nContext: wf-incident needs additional reasoning capacity.\n"
        "wf-analytics (background) has spare budget and contributes 30 %\n"
        "of its allocation temporarily.\n"
    )

    elasticity_engine = ElasticOperationalResourceEngine()

    adj = elasticity_engine.transfer(
        source_workflow="wf-analytics",
        target_workflow="wf-incident",
        resource_id="reasoning_capacity",
        source_capacity=1.0,
        requested_amount=0.30,
        duration_hint="until_incident_resolved",
    )

    print(render_resource_adjustment(adj))

    _section("Outcome")
    print(
        "wf-analytics contributed 30 % of its reasoning capacity to wf-incident.\n"
        "Transfer is temporary and will reverse automatically when the incident clears."
    )


# ── Scenario CT — Optimization Deferral ───────────────────────────────────────

def scenario_ct() -> None:
    _divider("Scenario CT — Optimization Deferral")
    print(
        "\nContext: Resource pressure spikes to 0.72 during a peak operational window.\n"
        "Background optimization passes for wf-analytics are deferred\n"
        "so that active workflows retain full planning capacity.\n"
    )

    pipeline = DistributedNegotiationPipeline()

    workflows = [
        WorkflowSnapshot("wf-incident",   "critical",   "critical",   0.90),
        WorkflowSnapshot("wf-analytics",  "background", "background", 0.45),
    ]

    outcome = pipeline.run(
        workflows=workflows,
        resource_pressure=0.72,
        pending_approvals=1,
    )

    print(outcome["report"])

    _section("Deferral Summary")
    print(
        "Background optimization for wf-analytics has been deferred.\n"
        "Active workflows retain full planning capacity during peak window.\n"
        "Optimization will resume when resource pressure drops below 0.55."
    )


# ── Scenario CU — Governance Batching ─────────────────────────────────────────

def scenario_cu() -> None:
    _divider("Scenario CU — Governance Batching")
    print(
        "\nContext: 6 governance approval reviews are pending across workflows.\n"
        "Instead of interrupting operations sequentially, reviews are batched\n"
        "and coordinated in a scheduled review window.\n"
    )

    pipeline = DistributedNegotiationPipeline()

    workflows = [
        WorkflowSnapshot("wf-procurement", "standard", "standard", 0.60),
        WorkflowSnapshot("wf-travel",      "low",      "low",      0.40),
        WorkflowSnapshot("wf-onboarding",  "standard", "standard", 0.55),
    ]

    outcome = pipeline.run(
        workflows=workflows,
        resource_pressure=0.55,
        pending_approvals=6,
    )

    print(outcome["report"])

    _section("Governance Coordination Note")
    print(
        "6 pending approval reviews have been batched into a coordinated review window.\n"
        "No governance requirement is permanently deferred.\n"
        "Batching dissolves automatically when the backlog clears."
    )


# ── Scenario CV — Negotiated Multi-Workflow Coordination ──────────────────────

def scenario_cv() -> None:
    _divider("Scenario CV — Negotiated Multi-Workflow Coordination")
    print(
        "\nContext: Resource pressure is critical (0.91).\n"
        "wf-incident (critical) must maintain full capacity.\n"
        "wf-travel (low) and wf-analytics (background) both contribute\n"
        "to absorb the pressure collaboratively.\n"
    )

    pipeline = DistributedNegotiationPipeline()

    workflows = [
        WorkflowSnapshot("wf-incident",  "critical",   "critical",   0.92),
        WorkflowSnapshot("wf-travel",    "low",        "low",        0.38),
        WorkflowSnapshot("wf-analytics", "background", "background", 0.30),
    ]

    outcome = pipeline.run(
        workflows=workflows,
        resource_pressure=0.91,
        pending_approvals=2,
    )

    print(outcome["report"])

    _section("Coordination Outcome")
    print(
        "Multiple workflows contributed to absorbing operational pressure.\n"
        "wf-incident continues at full capacity.\n"
        "wf-travel and wf-analytics operate temporarily at reduced depth.\n"
        "All adjustments are reversible and bounded."
    )


# ── Scenario CW — Recovery + Reversal ─────────────────────────────────────────

def scenario_cw() -> None:
    _divider("Scenario CW — Recovery + Reversal")
    print(
        "\nContext: Resource pressure has normalised (dropped to 0.40).\n"
        "All temporary degradation contracts for wf-reporting are now reverted.\n"
        "Operational quality is restored to baseline.\n"
    )

    # Set up a contract that we will then revert
    contracts_engine = OperationalNegotiationContractEngine()
    contract = contracts_engine.create(
        workflow_id="wf-reporting",
        contract_type="degradation",
        extra_terms={"mode": "reduced_reasoning", "reason": "pressure_spike"},
        expiry_trigger="resource_pressure_below_0.55",
    )

    print("Active contract before recovery:")
    print(render_negotiation_contract(contract))

    # Simulate pressure normalisation → revert
    reverted = contracts_engine.revert(contract.contract_id)

    _section("After Pressure Normalisation")
    if reverted:
        print(render_negotiation_contract(reverted))

    degradation_engine = GracefulOperationalDegradationEngine()
    from freya.negotiation.models import WorkflowDegradationPlan
    degraded_plan = WorkflowDegradationPlan(
        workflow_id="wf-reporting",
        degradation_mode="reduced_reasoning",
        reduced_capabilities=["deep analysis", "multi-step reasoning"],
        expected_quality_impact="Shallower analysis; multi-step reasoning replaced by heuristics.",
        reversibility=True,
        recovery_trigger="resource_pressure_below_0.55",
        minimum_quality_floor=0.35,
    )
    restored_plan = degradation_engine.recovery_plan(degraded_plan)
    print(render_degradation_plan(restored_plan))

    _section("Recovery Note")
    print(
        "wf-reporting has returned to full operational quality.\n"
        "All suspended capabilities have been restored.\n"
        "No permanent degradation occurred."
    )


# ── Scenario CX — Organizational Negotiation Summary ──────────────────────────

def scenario_cx() -> None:
    _divider("Scenario CX — Organizational Negotiation Summary")
    print(
        "\nContext: Full organizational snapshot during a moderate pressure period.\n"
        "Four workflows active; governance backlog at 3 pending reviews.\n"
        "Negotiation layer provides a complete distributed coordination view.\n"
    )

    pipeline = DistributedNegotiationPipeline()

    workflows = [
        WorkflowSnapshot("wf-incident",    "critical",   "critical",   0.78),
        WorkflowSnapshot("wf-procurement", "high",       "high",       0.65),
        WorkflowSnapshot("wf-travel",      "low",        "low",        0.42),
        WorkflowSnapshot("wf-analytics",   "background", "background", 0.28),
    ]

    outcome = pipeline.run(
        workflows=workflows,
        resource_pressure=0.78,
        pending_approvals=3,
    )

    print(outcome["report"])

    _section("Contract Ledger")
    summary = pipeline.contract_summary()
    print(f"  Active:   {summary.get('active', 0)}")
    print(f"  Expired:  {summary.get('expired', 0)}")
    print(f"  Reverted: {summary.get('reverted', 0)}")
    print(f"  Pending:  {summary.get('pending', 0)}")

    _section("Distributed Coordination Summary")
    print(
        "The negotiation layer has coordinated across all active workflows.\n"
        "Resource pressure is managed through elastic contribution and selective deferral.\n"
        "Governance reviews remain on track.\n"
        "All coordination is bounded, reversible, and auditable."
    )


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    print("\nFreya SDK — Distributed Operational Negotiation Demo")
    print("Demonstrating governance-preserving, adaptive workflow coordination.\n")

    scenario_cr()
    scenario_cs()
    scenario_ct()
    scenario_cu()
    scenario_cv()
    scenario_cw()
    scenario_cx()

    print("\n" + "═" * 70)
    print("  All scenarios completed.")
    print("  Freya negotiation layer: collaborative · adaptive · governed.")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    main()
