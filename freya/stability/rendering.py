"""freya/stability/rendering.py

Human-centered terminal rendering for the Operational Stabilization layer.

Design rules:
  - Collaborative, not punitive
  - Executive-friendly, concise
  - Instability is clear but constructive
  - No scoring language, no judgment
"""
from __future__ import annotations

from freya.stability.models import (
    AdaptiveTrustState,
    OperationalStabilityState,
    OperationalWeightProfile,
    StabilizationRecommendation,
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

_DRIFT_COLOURS = {
    "none":     _GREEN,
    "mild":     _CYAN,
    "moderate": _YELLOW,
    "severe":   _RED,
}
_TRUST_COLOURS = {
    "established": _GREEN,
    "standard":    _CYAN,
    "cautious":    _YELLOW,
    "restricted":  _RED,
}
_SCRUTINY_COLOURS = {
    "minimal":  _GREEN,
    "standard": _CYAN,
    "elevated": _YELLOW,
    "high":     _MAGENTA,
    "maximum":  _RED,
}
_TREND_COLOURS = {
    "improving": _GREEN,
    "stable":    _CYAN,
    "declining": _YELLOW,
}


def render_stability_state(state: OperationalStabilityState) -> str:
    drift_colour = _DRIFT_COLOURS.get(state.drift_level, "")
    score_pct    = int(state.stability_score * 100)

    if state.stability_score >= 0.80:
        score_str = f"{_GREEN}{score_pct}% — Stable{_RESET}"
    elif state.stability_score >= 0.55:
        score_str = f"{_YELLOW}{score_pct}% — Moderate{_RESET}"
    else:
        score_str = f"{_RED}{score_pct}% — Unstable{_RESET}"

    lines = [
        _DIVIDER,
        f"{_BOLD}  Operational Stability  —  {state.workflow_id}{_RESET}",
        "",
        f"  Stability Score:   {score_str}",
        f"  Drift Level:       {drift_colour}{state.drift_level.title()}{_RESET}",
        f"  Priority Reversals: {state.reversal_count}",
        f"  Active Mode:       {state.active_operational_mode.replace('_', ' ').title()}",
    ]
    if state.stabilization_recommended:
        lines.append(
            f"\n  {_YELLOW}⚠  Stabilization recommended — "
            f"see recommendation below.{_RESET}"
        )
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_trust_state(state: AdaptiveTrustState) -> str:
    trust_colour    = _TRUST_COLOURS.get(state.trust_level, "")
    scrutiny_colour = _SCRUTINY_COLOURS.get(state.governance_scrutiny, "")
    trend_colour    = _TREND_COLOURS.get(state.trust_trend, "")

    lines = [
        _DIVIDER,
        f"{_BOLD}  Adaptive Trust State  —  {state.workflow_id}{_RESET}",
        "",
        f"  Trust Level:       {trust_colour}{state.trust_level.title()}{_RESET}",
        f"  Governance Scrutiny: {scrutiny_colour}{state.governance_scrutiny.title()}{_RESET}",
        f"  Trust Trend:       {trend_colour}{state.trust_trend.title()}{_RESET}",
        f"  Compliant Streak:  {state.compliant_action_streak} action(s)",
        f"  Bypass Attempts:   {state.total_bypass_attempts}",
    ]
    if state.recent_governance_events:
        lines.append("")
        lines.append(f"  {_BOLD}Recent Governance Events{_RESET}")
        for ev in state.recent_governance_events[-3:]:
            lines.append(f"    {_DIM}• {ev}{_RESET}")
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_stabilization_recommendation(rec: StabilizationRecommendation) -> str:
    lines = [
        _DIVIDER,
        f"{_YELLOW}{_BOLD}  {rec.title}{_RESET}",
        "",
        f"  {rec.reason}",
        "",
        f"  {_BOLD}Recommended Mode:{_RESET} "
        f"{rec.recommended_mode.replace('_', ' ').title()}",
        f"  {_BOLD}Expected Impact:{_RESET}  {rec.expected_impact}",
    ]
    if rec.options:
        lines.append("")
        lines.append(f"  {_BOLD}Available Modes{_RESET}")
        for i, opt in enumerate(rec.options, 1):
            lines.append(f"    {i}. {opt}")
    lines.append("")
    lines.append(
        f"  {_DIM}You remain in control — choose a mode or continue with current direction.{_RESET}"
    )
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_weight_profile(profile: OperationalWeightProfile) -> str:
    lines = [
        _DIVIDER,
        f"{_BOLD}  Operational Preference Weight Profile{_RESET}",
        "",
    ]

    if profile.hard_constraints:
        lines.append(f"  {_BOLD}Hard Constraints{_RESET}  {_DIM}(non-negotiable){_RESET}")
        for k, v in profile.hard_constraints.items():
            lines.append(f"    • {k.replace('_',' ').title()}: {v}")
        lines.append("")

    if profile.soft_constraints:
        lines.append(f"  {_BOLD}Soft Constraints{_RESET}  {_DIM}(tradeable){_RESET}")
        for k, v in profile.soft_constraints.items():
            label = str(v) if not isinstance(v, bool) else ("✓" if v else "✗")
            lines.append(f"    • {k.replace('_',' ').title()}: {label}")
        lines.append("")

    if profile.weighted_preferences:
        lines.append(f"  {_BOLD}Preference Weights{_RESET}  {_DIM}(0.0 – 1.0){_RESET}")
        for dim, w in sorted(profile.weighted_preferences.items(), key=lambda x: -x[1]):
            if dim == "governance":
                continue
            filled = int(w * 10)
            bar = f"{_GREEN}{'█' * filled}{_DIM}{'░' * (10 - filled)}{_RESET}"
            lines.append(f"    {dim:<15} {bar}  {w:.1f}")
        lines.append("")

    if profile.operational_priorities:
        priority_str = " > ".join(
            p.title() for p in profile.operational_priorities if p != "governance"
        )
        lines.append(f"  {_BOLD}Priority Order:{_RESET}  {priority_str}")

    lines.append(_DIVIDER)
    return "\n".join(lines)
