"""examples/organizational_cognition_demo.py

Demonstrates the Organizational Policy + Multi-Workflow Cognition layer (Step 37).

Scenarios
---------
CK  Domain-aware governance           — finance vs travel vs incident-response
CL  Shared budget coordination        — multiple workflows compete for budget
CM  Workflow prioritization           — incident-response receives priority
CN  Resource contention               — shared reasoning budget nearing limit
CO  Governance load balancing         — approval backlog changes behavior
CP  Cross-workflow coordination       — optimization strategies coordinated
CQ  Organizational coordination summary — full org state rendered

Run
---
    python examples/organizational_cognition_demo.py
"""
from __future__ import annotations

import asyncio

from freya.org import (
    OrganizationalCognitionPipeline,
    OrganizationalPolicyEngine,
    OrganizationalWorkflowContext,
    SharedOperationalResource,
    render_org_policy,
    render_org_summary,
    render_prioritization_decision,
    render_resource_pressure,
    render_workflow_coordination,
)

# ── ANSI helpers ──────────────────────────────────────────────────────────────
_BOLD  = "\033[1m"
_CYAN  = "\033[96m"
_GREEN = "\033[92m"
_RESET = "\033[0m"
_WIDTH = 68


def _header(tag: str, title: str) -> None:
    print()
    print(f"{_CYAN}{'═' * _WIDTH}{_RESET}")
    print(f"  {_BOLD}Scenario {tag}: {title}{_RESET}")
    print(f"{_CYAN}{'═' * _WIDTH}{_RESET}")


# ── Shared fixtures ───────────────────────────────────────────────────────────
_policy_engine = OrganizationalPolicyEngine()
_pipeline      = OrganizationalCognitionPipeline()


def _wf(
    wf_id: str,
    domain: str,
    criticality: str = "standard",
    priority: str = "standard",
    budget_weight: float = 1.0,
    resource_groups: list[str] | None = None,
) -> OrganizationalWorkflowContext:
    return OrganizationalWorkflowContext(
        workflow_id=wf_id,
        workflow_domain=domain,
        operational_criticality=criticality,  # type: ignore[arg-type]
        organizational_priority=priority,
        execution_budget_weight=budget_weight,
        shared_resource_groups=resource_groups or [],
    )


# ── Scenario CK ───────────────────────────────────────────────────────────────
def scenario_ck() -> None:
    """CK — Domain-aware governance: finance vs travel vs incident-response."""
    _header("CK", "Domain-Aware Governance — Policy Per Domain")

    domains = [
        ("incident_response", "wf-incident"),
        ("finance",           "wf-finance"),
        ("travel",            "wf-travel"),
        ("security",          "wf-security"),
    ]
    for domain, wf_id in domains:
        policy = _policy_engine.resolve(domain)
        print(f"\n  Workflow: {wf_id}  ({domain})")
        print(render_org_policy(policy))


# ── Scenario CL ───────────────────────────────────────────────────────────────
def scenario_cl() -> None:
    """CL — Shared budget coordination across competing workflows."""
    _header("CL", "Shared Budget Coordination — Competing Workflows")

    workflows = [
        _wf("wf-travel-1",    "travel",   "standard", budget_weight=1.0, resource_groups=["reasoning_pool"]),
        _wf("wf-travel-2",    "travel",   "low",      budget_weight=0.8, resource_groups=["reasoning_pool"]),
        _wf("wf-analytics",   "research", "low",      budget_weight=0.6, resource_groups=["reasoning_pool"]),
        _wf("wf-incident",    "incident", "critical", budget_weight=2.0, resource_groups=["reasoning_pool"]),
    ]

    # Build shared resource with high pressure
    reasoning_pool = SharedOperationalResource(
        resource_id="reasoning_pool",
        resource_type="reasoning_budget",
        total_capacity=1.0,
        active_workflows=["wf-travel-1", "wf-travel-2", "wf-analytics", "wf-incident"],
        contention_level="high",
        resource_pressure=0.82,
        allocated={
            "wf-travel-1":  0.22,
            "wf-travel-2":  0.18,
            "wf-analytics": 0.17,
            "wf-incident":  0.25,
        },
    )

    result = _pipeline.run(
        workflows=workflows,
        resources=[reasoning_pool],
        pending_escalations=2,
        pending_approvals=3,
    )
    print(render_resource_pressure(result["resources"]))
    print(render_org_summary(result["cognition"]))


# ── Scenario CM ───────────────────────────────────────────────────────────────
def scenario_cm() -> None:
    """CM — Incident-response workflow receives organizational priority."""
    _header("CM", "Workflow Prioritization — Incident-Response Priority")

    workflows = [
        _wf("wf-reporting",  "research",          "low",      budget_weight=0.6),
        _wf("wf-travel-ops", "travel",            "standard", budget_weight=1.0),
        _wf("wf-incident",   "incident_response", "critical", budget_weight=2.0),
        _wf("wf-finance",    "finance",            "high",     budget_weight=1.2),
    ]
    result = _pipeline.run(workflows=workflows, resources=[])
    cognition = result["cognition"]

    print(f"\n  Workflow priority ranking:\n")
    for i, wf in enumerate(cognition.prioritization.ordered, 1):
        marker = " ← TOP" if i == 1 else ""
        print(
            f"  {i}. {wf.workflow_id:<20} domain={wf.workflow_domain:<22} "
            f"criticality={wf.operational_criticality}{marker}"
        )

    print()
    print(render_prioritization_decision(cognition.coordination_decisions))


# ── Scenario CN ───────────────────────────────────────────────────────────────
def scenario_cn() -> None:
    """CN — Shared reasoning budget nearing organizational limit."""
    _header("CN", "Resource Contention — Reasoning Budget Near Limit")

    workflows = [
        _wf("wf-a", "travel",   "standard"),
        _wf("wf-b", "research", "low"),
        _wf("wf-c", "finance",  "high"),
    ]

    # Severe pressure on reasoning and approval bandwidth
    reasoning = SharedOperationalResource(
        resource_id="reasoning_budget",
        resource_type="reasoning_budget",
        total_capacity=1.0,
        active_workflows=["wf-a", "wf-b", "wf-c"],
        contention_level="severe",
        resource_pressure=0.92,
        allocated={"wf-a": 0.35, "wf-b": 0.30, "wf-c": 0.27},
    )
    approval_bw = SharedOperationalResource(
        resource_id="approval_bandwidth",
        resource_type="approval_bandwidth",
        total_capacity=1.0,
        active_workflows=["wf-a", "wf-c"],
        contention_level="moderate",
        resource_pressure=0.65,
        allocated={"wf-a": 0.35, "wf-c": 0.30},
    )

    result = _pipeline.run(
        workflows=workflows,
        resources=[reasoning, approval_bw],
        pending_escalations=4,
    )
    print(render_resource_pressure(result["resources"]))
    print(render_workflow_coordination(result["plan"]))


# ── Scenario CO ───────────────────────────────────────────────────────────────
def scenario_co() -> None:
    """CO — Governance approval backlog changes workflow behavior."""
    _header("CO", "Governance Load Balancing — Approval Backlog")

    workflows = [
        _wf("wf-low-1",    "travel",   "low"),
        _wf("wf-low-2",    "research", "low"),
        _wf("wf-critical", "incident", "critical"),
    ]

    result = _pipeline.run(
        workflows=workflows,
        resources=[],
        pending_escalations=6,
        pending_approvals=9,     # high backlog
    )

    cognition = result["cognition"]
    plan      = result["plan"]

    print(f"  Governance backlog: {cognition.contention.governance_backlog} pending approvals")
    print(f"  Escalation load:   {cognition.contention.escalation_load}")
    print()
    print(render_workflow_coordination(plan))


# ── Scenario CP ───────────────────────────────────────────────────────────────
def scenario_cp() -> None:
    """CP — Cross-workflow optimization strategy coordination."""
    _header("CP", "Cross-Workflow Coordination — Optimization Strategies")

    workflows = [
        _wf("wf-exec",     "executive",  "high",       budget_weight=1.5),
        _wf("wf-travel-a", "travel",     "standard",   budget_weight=1.0),
        _wf("wf-travel-b", "travel",     "low",        budget_weight=0.7),
        _wf("wf-bg-tasks", "research",   "background", budget_weight=0.3),
    ]

    optimization_pool = SharedOperationalResource(
        resource_id="optimization_budget",
        resource_type="optimization_budget",
        total_capacity=1.0,
        active_workflows=["wf-exec", "wf-travel-a", "wf-travel-b", "wf-bg-tasks"],
        contention_level="high",
        resource_pressure=0.80,
        allocated={
            "wf-exec":     0.30,
            "wf-travel-a": 0.25,
            "wf-travel-b": 0.15,
            "wf-bg-tasks": 0.10,
        },
    )

    result = _pipeline.run(
        workflows=workflows,
        resources=[optimization_pool],
        pending_approvals=2,
    )

    print(render_workflow_coordination(result["plan"]))
    print(render_resource_pressure(result["resources"]))


# ── Scenario CQ ───────────────────────────────────────────────────────────────
def scenario_cq() -> None:
    """CQ — Full organizational operational state summary."""
    _header("CQ", "Organizational Coordination Summary")

    workflows = [
        _wf("wf-incident",    "incident_response", "critical", budget_weight=2.0,
            resource_groups=["reasoning_pool", "approval_bandwidth"]),
        _wf("wf-finance-01",  "finance",           "high",     budget_weight=1.2,
            resource_groups=["approval_bandwidth"]),
        _wf("wf-travel-ops",  "travel_operations", "standard", budget_weight=1.0,
            resource_groups=["reasoning_pool"]),
        _wf("wf-analytics",   "research",           "low",      budget_weight=0.5,
            resource_groups=["reasoning_pool"]),
        _wf("wf-bg-report",   "research",           "background", budget_weight=0.2),
    ]

    reasoning_pool = SharedOperationalResource(
        resource_id="reasoning_pool",
        resource_type="reasoning_budget",
        total_capacity=1.0,
        active_workflows=["wf-incident", "wf-travel-ops", "wf-analytics"],
        contention_level="moderate",
        resource_pressure=0.72,
        allocated={"wf-incident": 0.35, "wf-travel-ops": 0.22, "wf-analytics": 0.15},
    )
    approval_bw = SharedOperationalResource(
        resource_id="approval_bandwidth",
        resource_type="approval_bandwidth",
        total_capacity=1.0,
        active_workflows=["wf-incident", "wf-finance-01"],
        contention_level="low",
        resource_pressure=0.50,
        allocated={"wf-incident": 0.30, "wf-finance-01": 0.20},
    )

    result = _pipeline.run(
        workflows=workflows,
        resources=[reasoning_pool, approval_bw],
        pending_escalations=2,
        pending_approvals=5,
    )

    print(render_org_summary(result["cognition"]))
    print(render_resource_pressure(result["resources"]))
    print(render_workflow_coordination(result["plan"]))


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    scenario_ck()
    scenario_cl()
    scenario_cm()
    scenario_cn()
    scenario_co()
    scenario_cp()
    scenario_cq()

    print()
    print(f"{_CYAN}{'═' * _WIDTH}{_RESET}")
    print(f"  {_BOLD}Demo complete.{_RESET}  All 7 scenarios processed.")
    print(f"{_CYAN}{'═' * _WIDTH}{_RESET}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
