"""freya/context/rendering.py

Human-centered terminal rendering for the Contextual Operational Cognition layer.

Design rules:
  - Operational, executive-friendly, concise
  - No chain-of-thought exposed
  - No chatbot-style prose
  - Risk / instability is visually prominent
"""
from __future__ import annotations

from freya.context.models import (
    ContextualInterpretation,
    OperationalContext,
    OperationalTrajectory,
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

_MODE_LABELS = {
    "cost_sensitive":       f"{_GREEN}Cost-Sensitive Planning{_RESET}",
    "speed_optimized":      f"{_CYAN}Speed-Optimized Execution{_RESET}",
    "quality_focused":      f"{_MAGENTA}Quality-Focused Planning{_RESET}",
    "balanced":             f"{_RESET}Balanced{_RESET}",
    "governance_restricted": f"{_RED}Governance-Restricted{_RESET}",
    "unknown":              f"{_DIM}Unknown{_RESET}",
}
_RISK_COLOURS = {
    "none":     _GREEN,
    "low":      _CYAN,
    "medium":   _YELLOW,
    "high":     _MAGENTA,
    "critical": _RED,
}
_DRIFT_COLOURS = {
    "none":     _GREEN,
    "mild":     _CYAN,
    "moderate": _YELLOW,
    "severe":   _RED,
}


def render_operational_context(ctx: OperationalContext) -> str:
    """Render an OperationalContext summary panel."""
    mode_label = _MODE_LABELS.get(ctx.operational_mode, ctx.operational_mode)
    lines = [
        _DIVIDER,
        f"{_BOLD}  Operational Context  —  {ctx.workflow_id}{_RESET}",
        "",
        f"  State:            {ctx.workflow_state}",
        f"  Mode:             {mode_label}",
        f"  Strategy:         {ctx.execution_strategy}",
    ]

    if ctx.active_constraints:
        lines.append("")
        lines.append(f"  {_BOLD}Active Constraints{_RESET}")
        for k, v in ctx.active_constraints.items():
            lines.append(f"    • {k.replace('_',' ').title()}: {v}")

    if ctx.active_preferences:
        lines.append("")
        lines.append(f"  {_BOLD}Active Preferences{_RESET}")
        for k, v in ctx.active_preferences.items():
            lines.append(f"    • {k.replace('_',' ').title()}: {v}")

    if ctx.prior_guidance:
        lines.append("")
        lines.append(f"  {_BOLD}Recent Guidance{_RESET}")
        for g in ctx.prior_guidance[-5:]:
            lines.append(f"    • {g}")

    if ctx.optimization_history:
        lines.append("")
        lines.append(f"  {_BOLD}Optimization History{_RESET}")
        for o in ctx.optimization_history[-3:]:
            lines.append(f"    • {o}")

    gov_ok = not ctx.governance_history
    gov_status = f"{_GREEN}Normal{_RESET}" if gov_ok else f"{_YELLOW}Events recorded{_RESET}"
    lines.append("")
    lines.append(f"  Governance Status: {gov_status}")
    if ctx.governance_history:
        for g in ctx.governance_history[-3:]:
            lines.append(f"    {_DIM}• {g}{_RESET}")

    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_contextual_reasoning(interpretation: ContextualInterpretation) -> str:
    """Render how a single instruction was interpreted in context."""
    risk_colour = _RISK_COLOURS.get(interpretation.contextual_risk, "")
    conf_pct = int(interpretation.confidence_score * 100)
    if interpretation.confidence_score >= 0.80:
        conf_str = f"{_GREEN}High ({conf_pct}%){_RESET}"
    elif interpretation.confidence_score >= 0.60:
        conf_str = f"{_CYAN}Medium ({conf_pct}%){_RESET}"
    elif interpretation.confidence_score >= 0.40:
        conf_str = f"{_YELLOW}Low ({conf_pct}%){_RESET}"
    else:
        conf_str = f"{_RED}Very Low ({conf_pct}%){_RESET}"

    lines = [
        _DIVIDER,
        f"{_BOLD}  Contextual Interpretation{_RESET}",
        "",
        f"  Input:     {_DIM}\"{interpretation.raw_input[:72]}\"{_RESET}",
        f"  Meaning:   {interpretation.interpreted_meaning}",
        f"  Confidence: {conf_str}",
        f"  Risk:       {risk_colour}{interpretation.contextual_risk.title()}{_RESET}",
    ]

    if interpretation.contextual_reasoning:
        lines.append("")
        lines.append(f"  {_BOLD}Contextual Reasoning{_RESET}")
        for reason in interpretation.contextual_reasoning:
            lines.append(f"    • {reason}")

    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_operational_trajectory(traj: OperationalTrajectory) -> str:
    """Render an OperationalTrajectory panel."""
    drift_colour = _DRIFT_COLOURS.get(traj.execution_drift or "none", "")
    drift_label  = (traj.execution_drift or "None").title()

    gov_colour = _GREEN if traj.governance_pattern == "clean" else _YELLOW
    if "escalating" in traj.governance_pattern:
        gov_colour = _RED

    lines = [
        _DIVIDER,
        f"{_BOLD}  Operational Trajectory  —  {traj.trajectory_id}{_RESET}",
        "",
        f"  Optimization Direction: {traj.optimization_direction.replace('_',' ').title()}",
        f"  Governance Pattern:     {gov_colour}{traj.governance_pattern.replace('_',' ').title()}{_RESET}",
        f"  Execution Drift:        {drift_colour}{drift_label}{_RESET}",
    ]

    if traj.prior_decisions:
        lines.append("")
        lines.append(f"  {_BOLD}Recent Decisions{_RESET}")
        for d in traj.prior_decisions[-5:]:
            lines.append(f"    • {d}")

    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_drift_warnings(warnings: list[str]) -> str:
    """Render instability / drift warnings."""
    if not warnings:
        return f"{_GREEN}  ✓ No operational instability detected.{_RESET}"
    lines = [
        _DIVIDER,
        f"{_YELLOW}{_BOLD}  ⚠  Operational Instability Detected{_RESET}",
        "",
    ]
    for w in warnings:
        lines.append(f"  {_YELLOW}• {w}{_RESET}")
    lines.append(_DIVIDER)
    return "\n".join(lines)
