"""freya/negotiation/rendering.py

Human-readable rendering for all negotiation layer data structures.
Output style: collaborative, executive-friendly.
No swarm-chat language; no jargon; no blaming.
"""
from __future__ import annotations

from freya.negotiation.models import (
    ElasticResourceAdjustment,
    NegotiationContract,
    NegotiationProposal,
    WorkflowDegradationPlan,
)


# ── Top-level renderers ────────────────────────────────────────────────────────

def render_negotiation_summary(proposal: NegotiationProposal) -> str:
    """Render an executive summary of a negotiation proposal."""
    lines = [
        "┌─ Negotiation Proposal ─────────────────────────────────────────────┐",
        f"│  ID:            {proposal.proposal_id}",
        f"│  Strategy:      {_fmt_strategy(proposal.strategy_used)}",
        f"│  Workflows:     {', '.join(proposal.participating_workflows)}",
        f"│  Gov. risk:     {proposal.governance_risk.upper()}",
        f"│  Confidence:    {proposal.confidence_score:.0%}",
        "│",
        "│  Adjustments:",
    ]
    for item in proposal.proposed_adjustments:
        lines.append(f"│    • {item}")
    lines.append("│")
    lines.append(f"│  Expected impact: {proposal.expected_operational_impact}")
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_degradation_plan(plan: WorkflowDegradationPlan) -> str:
    """Render a human-readable summary of a workflow degradation plan."""
    rev = "Yes — restored when pressure normalises" if plan.reversibility else "No"
    lines = [
        "┌─ Operational Adjustment Plan ──────────────────────────────────────┐",
        f"│  Workflow:      {plan.workflow_id}",
        f"│  Mode:          {_fmt_mode(plan.degradation_mode)}",
        f"│  Quality floor: {plan.minimum_quality_floor:.0%} (protected)",
        f"│  Reversible:    {rev}",
        f"│  Recovery:      {plan.recovery_trigger}",
        "│",
        f"│  Impact:        {plan.expected_quality_impact}",
    ]
    if plan.reduced_capabilities:
        lines.append("│  Suspended:     " + ", ".join(plan.reduced_capabilities))
    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_resource_adjustment(adj: ElasticResourceAdjustment) -> str:
    """Render a human-readable summary of a resource reallocation."""
    duration = adj.duration_hint or "until pressure normalises"
    lines = [
        "┌─ Resource Reallocation ─────────────────────────────────────────────┐",
        f"│  Resource:      {adj.resource_id}",
        f"│  From:          {adj.source_workflow}",
        f"│  To:            {adj.target_workflow}",
        f"│  Amount:        {adj.adjustment_amount:.1%} of capacity",
        f"│  Temporary:     {'Yes' if adj.temporary else 'No'}",
        f"│  Duration:      {duration}",
        "└─────────────────────────────────────────────────────────────────────┘",
    ]
    return "\n".join(lines)


def render_negotiation_contract(contract: NegotiationContract) -> str:
    """Render a contract record with terms and audit trail."""
    lines = [
        "┌─ Negotiation Contract ──────────────────────────────────────────────┐",
        f"│  Contract ID:   {contract.contract_id}",
        f"│  Workflow:      {contract.workflow_id}",
        f"│  Type:          {contract.contract_type.replace('_', ' ').title()}",
        f"│  Status:        {contract.status.upper()}",
        f"│  Reversible:    {'Yes' if contract.reversible else 'No'}",
        f"│  Expiry:        {contract.expiry_trigger}",
        "│  Terms:",
    ]
    for key, value in contract.terms.items():
        lines.append(f"│    • {key}: {value}")
    if contract.audit_log:
        lines.append("│  Audit log:")
        for entry in contract.audit_log[-3:]:          # Show last 3 entries
            lines.append(f"│    {entry}")
    lines.append("└─────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def render_full_negotiation_state(
    proposal: NegotiationProposal,
    plans: list[WorkflowDegradationPlan],
    adjustments: list[ElasticResourceAdjustment],
    contracts: list[NegotiationContract],
    approved: bool,
    violations: list[str],
) -> str:
    """Render the complete negotiation outcome in one coherent report."""
    sections: list[str] = [
        "═" * 70,
        "  DISTRIBUTED OPERATIONAL NEGOTIATION — CYCLE REPORT",
        "═" * 70,
        "",
        render_negotiation_summary(proposal),
    ]

    if plans:
        sections.append("\n── Degradation Plans ──")
        for plan in plans:
            sections.append(render_degradation_plan(plan))

    if adjustments:
        sections.append("\n── Resource Reallocations ──")
        for adj in adjustments:
            sections.append(render_resource_adjustment(adj))

    if contracts:
        sections.append("\n── Active Contracts ──")
        for contract in contracts:
            sections.append(render_negotiation_contract(contract))

    sections.append("")
    status_line = "✓ GOVERNANCE APPROVED" if approved else "✗ GOVERNANCE BLOCKED"
    sections.append(f"Governance Status:  {status_line}")
    if violations:
        for v in violations:
            sections.append(f"  ! {v}")

    sections.append("═" * 70)
    return "\n".join(sections)


# ── Private helpers ────────────────────────────────────────────────────────────

def _fmt_strategy(s: str) -> str:
    return s.replace("_", " ").title()


def _fmt_mode(m: str) -> str:
    return m.replace("_", " ").title() if m != "none" else "No Adjustment (Full Capacity)"
