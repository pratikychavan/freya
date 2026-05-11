"""freya/steering/rendering.py

Human-centered terminal rendering for the steering layer.

Design rules:
  - Concise, operational, business-oriented
  - No runtime jargon
  - Numbers are actionable (₹ amounts, hours saved)
  - Options are numbered for easy selection
  - Recommendations come after conflicts, never instead of them
"""
from __future__ import annotations

from freya.steering.models import (
    NegotiationProposal,
    SteeringDecision,
    WorkflowSteeringState,
)
from freya.steering.recommendations import OperationalRecommendation

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
_CHECK = "✓"
_WARN = "⚠"
_SPARK = "✦"
_BULLET = "•"
_ARROW = "→"
_STAR = "★"


def _header(text: str) -> str:
    return f"\n{_BOLD}{text}{_RESET}"


def _cost_delta(delta: float | None) -> str:
    if delta is None:
        return ""
    if delta > 0:
        return f"  {_RED}+₹{int(delta):,}{_RESET}"
    if delta < 0:
        return f"  {_GREEN}saves ₹{int(-delta):,}{_RESET}"
    return f"  {_DIM}no cost change{_RESET}"


def _time_delta(hours: float | None) -> str:
    if hours is None:
        return ""
    abs_h = abs(hours)
    label = f"{abs_h:.1f} hr" if abs_h != int(abs_h) else f"{int(abs_h)} hr"
    if hours < 0:
        return f"  {_GREEN}saves ~{label}{_RESET}"
    if hours > 0:
        return f"  {_YELLOW}adds ~{label}{_RESET}"
    return ""


def render_negotiation(proposal: NegotiationProposal) -> str:
    """Render a NegotiationProposal as a compact tradeoff panel."""
    lines: list[str] = []

    lines.append(_DIVIDER)
    lines.append(f"{_YELLOW}{_WARN}  Tradeoff Detected{_RESET}")
    lines.append("")
    lines.append(f"  {proposal.reason}")
    lines.append("")
    lines.append(f"{_BOLD}  Available Options{_RESET}")
    lines.append("")

    for i, opt in enumerate(proposal.options, 1):
        is_recommended = opt.option_id == proposal.recommended_option_id
        star = f" {_YELLOW}{_STAR} Recommended{_RESET}" if is_recommended else ""
        lines.append(f"  {_BOLD}{i}. {opt.title}{_RESET}{star}")
        lines.append(f"     {opt.description}")

        deltas: list[str] = []
        cd = _cost_delta(opt.estimated_cost_change)
        td = _time_delta(opt.estimated_time_change)
        if cd:
            deltas.append(cd.strip())
        if td:
            deltas.append(td.strip())
        if deltas:
            lines.append(f"     {_DIM}{' · '.join(deltas)}{_RESET}")
        lines.append("")

    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_recommendation(rec: OperationalRecommendation) -> str:
    """Render a single OperationalRecommendation."""
    priority_colour = {"high": _GREEN, "medium": _CYAN, "low": _DIM}.get(rec.priority, "")
    lines: list[str] = [
        _DIVIDER,
        f"{priority_colour}{_SPARK}  Recommendation{_RESET}",
        "",
        f"  {_BOLD}{rec.headline}{_RESET}",
        f"  {rec.rationale}",
        "",
        f"  {_DIM}{rec.impact_summary}{_RESET}",
    ]
    if rec.suggested_action:
        lines.append("")
        lines.append(f"  {_ARROW} {rec.suggested_action}")
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_recommendations(recs: list[OperationalRecommendation]) -> str:
    """Render multiple recommendations."""
    if not recs:
        return ""
    return "\n".join(render_recommendation(r) for r in recs)


def render_operational_update(decision: SteeringDecision) -> str:
    """Render the outcome of a SteeringDecision (what changed)."""
    lines: list[str] = [
        _DIVIDER,
        f"{_GREEN}{_CHECK}  Understood{_RESET}",
        "",
        f"  {decision.narrative}",
    ]
    if decision.applied_updates:
        lines.append("")
        lines.append(f"  {_DIM}Changes applied:{_RESET}")
        for k, v in decision.applied_updates.items():
            label = k.replace("_", " ").title()
            if k == "budget_inr" and isinstance(v, (int, float)):
                v = f"₹{int(v):,}"
            lines.append(f"    {_BULLET} {label}: {v}")
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_steering_state(state: WorkflowSteeringState) -> str:
    """Render a summary of the current WorkflowSteeringState."""
    lines: list[str] = [
        _DIVIDER,
        f"{_BOLD}  Current Operational State{_RESET}",
        "",
        f"  Goal:     {state.goal}",
        f"  Strategy: {state.strategy.title()}",
        f"  Priority: {state.priority.title()}",
    ]

    if state.constraints:
        lines.append("")
        lines.append(f"  {_BOLD}Constraints{_RESET}")
        for name, c in state.constraints.items():
            label = name.replace("_", " ").title()
            val = c.value
            if name == "budget_inr" and isinstance(val, (int, float)):
                val = f"₹{int(val):,}"
            negotiable = "" if c.negotiable else f"  {_DIM}(fixed){_RESET}"
            lines.append(f"    {_BULLET} {label}: {val}{negotiable}")

    if state.preferences:
        lines.append("")
        lines.append(f"  {_BOLD}Preferences{_RESET}")
        for p in state.preferences:
            label = p.preference_name.replace("_", " ").title()
            lines.append(f"    {_BULLET} {label}: {p.preference_value}")

    if state.decisions_made:
        lines.append("")
        lines.append(f"  {_BOLD}Decisions Made{_RESET}")
        for d in state.decisions_made:
            lines.append(f"    {_CHECK} {d.narrative}")

    lines.append(_DIVIDER)
    return "\n".join(lines)
