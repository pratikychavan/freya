"""freya/hitl/rendering.py

Human-centered terminal rendering for the Advanced HITL layer.
"""
from __future__ import annotations

from freya.hitl.models import (
    GuidanceApplicationResult,
    GuidanceGovernanceDecision,
    HumanGuidance,
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
_CHECK = "✓"
_CROSS = "✗"
_ARROW = "→"
_BULLET = "•"
_WARN = "⚠"
_LOCK = "🔒"


def render_guidance_prompt(
    context: str,
    reason: str,
    current_recommendation: str | None = None,
    show_guidance_option: bool = True,
) -> str:
    """Render the operational guidance prompt shown to the user.

    Parameters
    ----------
    context     : Short label for the checkpoint (e.g. "Hotel Selection")
    reason      : Why this checkpoint was triggered
    current_recommendation : What Freya currently proposes to do
    show_guidance_option : Whether to include the guidance input option
    """
    width = 66
    lines: list[str] = [
        "",
        f"{_CYAN}{'═' * width}{_RESET}",
        f"{_BOLD}  Approval Required — {context}{_RESET}",
        f"{_CYAN}{'═' * width}{_RESET}",
        "",
        f"  {_BOLD}Reason{_RESET}",
        f"  {reason}",
    ]
    if current_recommendation:
        lines += [
            "",
            f"  {_BOLD}Current Recommendation{_RESET}",
            f"  {current_recommendation}",
        ]
    lines += [
        "",
        f"  {_BOLD}Options{_RESET}",
        f"  [1] Approve",
        f"  [2] Reject",
    ]
    if show_guidance_option:
        lines += [
            f"  [3] Provide Operational Guidance",
            f"  [4] View Optimization Details",
        ]
    lines += [
        "",
        f"{_CYAN}{'─' * width}{_RESET}",
        f"  {_DIM}Example guidance: \"Find something cheaper\"  |  \"Prioritise metro access\"{_RESET}",
        f"{_CYAN}{'─' * width}{_RESET}",
        "",
    ]
    return "\n".join(lines)


def render_guidance_result(result: GuidanceApplicationResult) -> str:
    """Render the outcome of applying a HumanGuidance."""
    lines: list[str] = [_DIVIDER]

    if result.success:
        lines.append(f"{_GREEN}{_CHECK}  Guidance Applied{_RESET}")
    else:
        lines.append(f"{_YELLOW}{_WARN}  Guidance Noted{_RESET}")

    lines.append("")
    lines.append(f"  {result.narrative_summary}")

    if result.applied_changes:
        lines.append("")
        lines.append(f"  {_BOLD}Changes Applied{_RESET}")
        for ch in result.applied_changes:
            lines.append(f"    {_BULLET} {ch}")

    if result.workflow_updates:
        lines.append("")
        lines.append(f"  {_BOLD}Workflow Updates{_RESET}")
        for wu in result.workflow_updates:
            lines.append(f"    {_ARROW} {wu}")

    if result.governance_actions:
        lines.append("")
        lines.append(f"  {_BOLD}Governance{_RESET}")
        for ga in result.governance_actions:
            lines.append(f"    {_YELLOW}{_WARN}{_RESET} {ga}")

    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_guidance_review(
    guidance: HumanGuidance,
    decision: GuidanceGovernanceDecision,
) -> str:
    """Render the governance review result for a given guidance."""
    lines: list[str] = [_DIVIDER]

    risk_colour = {
        "none": _GREEN,
        "low": _CYAN,
        "medium": _YELLOW,
        "high": _RED,
    }.get(decision.risk_level, "")

    status = f"{_GREEN}{_CHECK} Allowed{_RESET}" if decision.allowed else f"{_RED}{_CROSS} Blocked{_RESET}"
    lines += [
        f"  {_BOLD}Governance Review{_RESET}",
        "",
        f"  Input:      \"{guidance.raw_input[:60]}\"",
        f"  Intent:     {guidance.interpreted_intent}",
        f"  Type:       {guidance.guidance_type.replace('_', ' ').title()}",
        f"  Status:     {status}",
        f"  Risk:       {risk_colour}{decision.risk_level.title()}{_RESET}",
        f"  Reason:     {decision.reason}",
    ]
    if decision.requires_approval:
        lines.append("")
        lines.append(f"  {_LOCK} Manual escalation required before this guidance can be applied.")
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_guidance_interpreted(guidance: HumanGuidance) -> str:
    """Compact rendering of the interpreted guidance — shown before applying."""
    conf = f"{guidance.confidence_score:.0%}"
    method = "AI" if guidance.parse_method == "llm" else "pattern"
    lines = [
        _DIVIDER,
        f"  {_DIM}Guidance interpreted ({method}, confidence {conf}){_RESET}",
        f"  {_BOLD}{guidance.interpreted_intent}{_RESET}",
    ]
    if guidance.extracted_constraints:
        for k, v in guidance.extracted_constraints.items():
            label = k.replace("_", " ").title()
            if k == "budget_target" and isinstance(v, (int, float)):
                v = f"₹{int(v):,}"
            lines.append(f"  {_BULLET} {label}: {v}")
    if guidance.extracted_preferences:
        for k, v in guidance.extracted_preferences.items():
            lines.append(f"  {_BULLET} {k.replace('_', ' ').title()}: {v}")
    lines.append(_DIVIDER)
    return "\n".join(lines)
