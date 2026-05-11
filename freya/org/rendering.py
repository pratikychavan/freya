"""freya/org/rendering.py

Human-centered terminal rendering for the Organizational Cognition layer.

Design rules:
  - Executive-friendly, concise, situationally aware
  - No engine telemetry; no bureaucratic overload
  - Decisions are visible and explained
  - Coordination is collaborative, never authoritarian
"""
from __future__ import annotations

from freya.org.cognition import OrgCognitionResult
from freya.org.contention import ContentionAnalysis
from freya.org.coordination import CoordinationPlan
from freya.org.models import (
    OrganizationalPolicy,
    SharedOperationalResource,
    WorkflowCoordinationDecision,
)

# ── ANSI ─────────────────────────────────────────────────────────────────────
_BOLD    = "\033[1m"
_DIM     = "\033[2m"
_CYAN    = "\033[96m"
_GREEN   = "\033[92m"
_YELLOW  = "\033[93m"
_MAGENTA = "\033[95m"
_RED     = "\033[91m"
_RESET   = "\033[0m"
_DIVIDER = f"{_CYAN}{'─' * 66}{_RESET}"

_CONTENTION_COLOURS = {
    "none":     _GREEN,
    "low":      _CYAN,
    "moderate": _YELLOW,
    "high":     _MAGENTA,
    "severe":   _RED,
}
_PRESSURE_COLOURS = {
    "none":     _GREEN,
    "low":      _CYAN,
    "moderate": _YELLOW,
    "high":     _MAGENTA,
    "critical": _RED,
}
_GOV_COLOURS = {
    "minimal":  _GREEN,
    "flexible": _CYAN,
    "standard": _CYAN,
    "strict":   _YELLOW,
}
_DECISION_ICONS = {
    "prioritize":      "🚀",
    "defer":           "⏸",
    "rebalance":       "⚖",
    "escalate":        "⬆",
    "reduce_reasoning":"⬇",
    "governance_gate": "🔒",
    "no_action":       "✓",
}


def render_org_policy(policy: OrganizationalPolicy) -> str:
    gov_colour = _GOV_COLOURS.get(policy.governance_level, "")
    lines = [
        _DIVIDER,
        f"{_BOLD}  Organizational Policy — {policy.policy_name}{_RESET}",
        "",
        f"  Governance Level:        {gov_colour}{policy.governance_level.title()}{_RESET}",
        f"  Reasoning Depth:         {policy.reasoning_depth}",
        f"  Clarification Threshold: {int(policy.clarification_threshold * 100)}%",
        f"  Auto-approve:            {'Yes' if policy.auto_approve else 'No'}",
    ]
    if policy.execution_constraints:
        lines.append("")
        lines.append(f"  {_BOLD}Execution Constraints{_RESET}")
        for k, v in policy.execution_constraints.items():
            lines.append(f"    • {k.replace('_',' ').title()}: {v}")
    if policy.optimization_limits:
        lines.append("")
        lines.append(f"  {_BOLD}Optimization Limits{_RESET}")
        for k, v in policy.optimization_limits.items():
            lines.append(f"    • {k.replace('_',' ').title()}: {v}")
    if policy.notes:
        lines.append("")
        lines.append(f"  {_DIM}{policy.notes[0]}{_RESET}")
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_workflow_coordination(plan: CoordinationPlan) -> str:
    lines = [
        _DIVIDER,
        f"{_BOLD}  Organizational Coordination Update{_RESET}",
        "",
    ]
    if plan.prioritized:
        lines.append(
            f"  {_GREEN}🚀 Prioritized:{_RESET}  {', '.join(plan.prioritized)}"
        )
    if plan.deferred:
        lines.append(
            f"  {_YELLOW}⏸ Deferred:{_RESET}     {', '.join(plan.deferred)}"
        )
    if plan.rebalanced:
        lines.append(
            f"  {_CYAN}⚖ Rebalanced:{_RESET}   {', '.join(plan.rebalanced)}"
        )

    if plan.decisions:
        lines.append("")
        lines.append(f"  {_BOLD}Coordination Decisions{_RESET}")
        for d in plan.decisions[:6]:  # cap at 6 for readability
            icon = _DECISION_ICONS.get(d.decision_type, "•")
            wf_list = ", ".join(d.affected_workflows)
            lines.append(f"  {icon}  [{d.decision_type}] {wf_list}")
            lines.append(f"     {_DIM}{d.reason[:90]}{_RESET}")
            lines.append(f"     Impact: {d.operational_impact[:80]}")

    if plan.rationale:
        lines.append("")
        lines.append(f"  {_BOLD}Rationale{_RESET}")
        for r in plan.rationale[:5]:
            lines.append(f"    • {r}")

    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_resource_pressure(resources: list[SharedOperationalResource]) -> str:
    lines = [
        _DIVIDER,
        f"{_BOLD}  Shared Operational Resources{_RESET}",
        "",
    ]
    if not resources:
        lines.append(f"  {_GREEN}No shared resources registered.{_RESET}")
    else:
        for res in resources:
            colour = _CONTENTION_COLOURS.get(res.contention_level, "")
            pct    = int(res.resource_pressure * 100)
            filled = pct // 10
            bar    = f"{colour}{'█' * filled}{_DIM}{'░' * (10 - filled)}{_RESET}"
            lines.append(
                f"  {res.resource_id:<28} {bar}  {pct:3d}%  "
                f"{colour}[{res.contention_level}]{_RESET}"
            )
            if res.active_workflows:
                wf_str = ", ".join(res.active_workflows[:4])
                lines.append(f"    {_DIM}Workflows: {wf_str}{_RESET}")
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_prioritization_decision(decisions: list[WorkflowCoordinationDecision]) -> str:
    if not decisions:
        return f"{_GREEN}  No coordination decisions required.{_RESET}"
    lines = [
        _DIVIDER,
        f"{_BOLD}  Workflow Prioritization Decisions{_RESET}",
        "",
    ]
    for d in decisions:
        icon = _DECISION_ICONS.get(d.decision_type, "•")
        wf_list = ", ".join(d.affected_workflows)
        lines.append(f"  {icon}  {_BOLD}{d.decision_type.replace('_',' ').title()}{_RESET}  →  {wf_list}")
        lines.append(f"     Reason: {d.reason[:100]}")
        lines.append(f"     Impact: {d.operational_impact[:90]}")
        lines.append("")
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_org_summary(result: OrgCognitionResult) -> str:
    pressure_colour = _PRESSURE_COLOURS.get(result.budget_pressure, "")
    lines = [
        _DIVIDER,
        f"{_BOLD}  Organizational Operational State{_RESET}",
        "",
    ]
    for s in result.org_summary:
        lines.append(f"  • {s}")
    lines.append("")
    lines.append(
        f"  Budget Pressure: {pressure_colour}{result.budget_pressure.title()}{_RESET}"
    )
    stable_str = f"{_GREEN}Stable{_RESET}" if result.is_stable() else f"{_YELLOW}Attention needed{_RESET}"
    lines.append(f"  Org State:       {stable_str}")
    lines.append(_DIVIDER)
    return "\n".join(lines)
