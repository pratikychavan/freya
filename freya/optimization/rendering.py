"""freya/optimization/rendering.py

Human-centered terminal rendering for the Proactive Optimization layer.

Design rules:
  - Executive-friendly: numbers first, jargon-free
  - Confidence drives language strength ("Strongly recommended" vs "Possible")
  - Approval requirements are prominent
  - No runtime internals visible
"""
from __future__ import annotations

from freya.optimization.models import (
    OptimizationEvaluation,
    OptimizationOpportunity,
    OptimizationProposal,
)

# ── ANSI ─────────────────────────────────────────────────────────────
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_MAGENTA = "\033[95m"
_RED = "\033[91m"
_RESET = "\033[0m"

_DIVIDER = f"{_CYAN}{'─' * 66}{_RESET}"
_SPARK = "✦"
_WARN = "⚠"
_CHECK = "✓"
_LOCK = "🔒"
_BULLET = "•"
_ARROW = "→"


def _delta_str(delta: float | None, unit: str = "₹", invert: bool = False) -> str:
    """Render a delta as a coloured string."""
    if delta is None:
        return ""
    val = -delta if invert else delta
    if val < 0:
        sign, colour = ("saves ", _GREEN)
    elif val > 0:
        sign, colour = ("+", _RED)
    else:
        return f"{_DIM}no change{_RESET}"

    if unit == "₹":
        return f"{colour}{sign}₹{int(abs(val)):,}{_RESET}"
    elif unit == "hr":
        return f"{colour}{sign}{abs(val):.1f} hr{_RESET}"
    return f"{colour}{sign}{abs(val)}{_RESET}"


def _confidence_badge(score: float) -> str:
    if score >= 0.85:
        return f"{_GREEN}■■■ {score:.0%}{_RESET}"
    if score >= 0.65:
        return f"{_CYAN}■■░ {score:.0%}{_RESET}"
    if score >= 0.45:
        return f"{_YELLOW}■░░ {score:.0%}{_RESET}"
    return f"{_DIM}░░░ {score:.0%}{_RESET}"


def render_optimization_proposal(proposal: OptimizationProposal) -> str:
    """Render a full OptimizationProposal as a terminal panel."""
    lines: list[str] = [_DIVIDER]

    # Header
    header_colour = _YELLOW if proposal.requires_approval else _CYAN
    lock = f" {_LOCK} Approval Required" if proposal.requires_approval else ""
    lines.append(f"{header_colour}{_SPARK}  Optimization Opportunity{_RESET}{lock}")
    lines.append("")
    lines.append(f"  {proposal.reason}")

    # Evaluation summary
    if proposal.evaluation:
        ev = proposal.evaluation
        lines.append("")
        lines.append(f"  {_BOLD}Summary{_RESET}")
        if ev.total_savings > 0:
            lines.append(f"    {_BULLET} Savings:          {_GREEN}₹{int(ev.total_savings):,}{_RESET}")
        lines.append(f"    {_BULLET} Execution Impact: {ev.execution_impact}")
        lines.append(f"    {_BULLET} Confidence:       {_confidence_badge(ev.confidence_score)}")
        if ev.governance_risk != "none":
            risk_colour = _YELLOW if ev.governance_risk == "low" else _MAGENTA
            lines.append(
                f"    {_BULLET} Governance Risk:  {risk_colour}{ev.governance_risk.title()}{_RESET}"
            )
        lines.append(f"    {_BULLET} Assessment:       {ev.confidence_label()}")

    # Individual opportunities
    lines.append("")
    lines.append(f"  {_BOLD}Opportunities{_RESET}")
    for i, opp in enumerate(proposal.opportunities, 1):
        is_approval = opp.governance_impact == "requires_approval"
        tag = f" {_YELLOW}[needs approval]{_RESET}" if is_approval else ""
        lines.append(f"")
        lines.append(f"  {i}. {_BOLD}{opp.title}{_RESET}{tag}")
        lines.append(f"     {opp.description}")

        deltas = []
        cd = _delta_str(opp.estimated_cost_delta, "₹")
        td = _delta_str(opp.estimated_time_delta, "hr")
        if cd:
            deltas.append(cd)
        if td:
            deltas.append(td)
        if deltas:
            lines.append(f"     {_DIM}{' · '.join(d.replace(_RESET, '') + _RESET for d in deltas)}{_RESET}")

    # Recommended action
    lines.append("")
    lines.append(f"  {_ARROW} {_BOLD}{proposal.recommended_action}{_RESET}")
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_optimization_summary(proposal: OptimizationProposal) -> str:
    """One-line summary for progress panels where space is limited."""
    ev = proposal.evaluation
    savings_str = f"₹{int(ev.total_savings):,}" if ev and ev.total_savings > 0 else "time savings"
    lock = " · approval needed" if proposal.requires_approval else ""
    return (
        f"{_SPARK} {len(proposal.opportunities)} optimization available · "
        f"save {savings_str}{lock}"
    )


def render_optimization_evaluation(evaluation: OptimizationEvaluation) -> str:
    """Render a standalone OptimizationEvaluation."""
    lines = [
        _DIVIDER,
        f"{_CYAN}  Workflow Optimization Score{_RESET}",
        "",
        f"  Estimated Savings:  {_GREEN}₹{int(evaluation.total_savings):,}{_RESET}"
            if evaluation.total_savings > 0
            else f"  Estimated Savings:  {_DIM}none{_RESET}",
        f"  Execution Impact:   {evaluation.execution_impact}",
        f"  Governance Risk:    {evaluation.governance_risk.title()}",
        f"  Confidence:         {_confidence_badge(evaluation.confidence_score)}",
        f"  Net Value Score:    {evaluation.net_value_score:+.2f}",
        f"  Assessment:         {evaluation.confidence_label()}",
        _DIVIDER,
    ]
    return "\n".join(lines)
