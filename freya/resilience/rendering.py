"""freya/resilience/rendering.py

Human-centered rendering for the resilience cognition layer.

Outputs are executive-friendly, continuity-aware, and strategically
grounded — not telemetry dumps or opaque optimization readouts.
"""
from __future__ import annotations

from freya.resilience.models import (
    AdaptationPortfolioState,
    ContinuityAssessment,
    OperationalResilienceReserve,
    OrganizationalIdentityProfile,
)


def _box(title: str, lines: list[str]) -> str:
    width = max(len(title), *(len(l) for l in lines), 50) + 4
    border = "─" * width
    rows = [f"┌{border}┐", f"│  {title.upper():<{width - 2}}│"]
    rows.append(f"├{border}┤")
    for line in lines:
        rows.append(f"│  {line:<{width - 2}}│")
    rows.append(f"└{border}┘")
    return "\n".join(rows)


def render_resilience_reserve(reserve: OperationalResilienceReserve) -> str:
    cap_pct = f"{reserve.current_capacity:.0%}"
    lines = [
        f"Reserve Type     : {reserve.reserve_type.upper()}",
        f"Remaining Cap.   : {cap_pct}",
        f"Depletion Risk   : {reserve.depletion_risk.upper()}",
        "Replenishment    :",
    ]
    for i in range(0, len(reserve.replenishment_strategy), 76):
        lines.append(f"  {reserve.replenishment_strategy[i:i+76]}")
    return _box(f"Resilience Reserve — {reserve.reserve_type}", lines)


def render_identity_assessment(profile: OrganizationalIdentityProfile) -> str:
    lines = [
        f"Identity         : {profile.identity_name}",
        f"Preservation     : {profile.preservation_priority.upper()}",
        "",
        "Protected Characteristics:",
    ]
    for c in profile.protected_characteristics:
        lines.append(f"  ✓ {c.replace('_', ' ')}")
    if profile.degradation_signals:
        lines.append("")
        lines.append("Degradation Signals:")
        for s in profile.degradation_signals:
            lines.append(f"  ⚠ {s.replace('_', ' ')}")
    else:
        lines.append("")
        lines.append("  No degradation signals detected.")
    return _box("Organizational Identity Assessment", lines)


def render_adaptation_portfolio(portfolio: AdaptationPortfolioState) -> str:
    score_pct = f"{portfolio.sustainability_score:.0%}"
    lines = [
        f"Rotation Balance : {portfolio.rotation_balance.upper()}",
        f"Sustainability   : {score_pct}",
        "",
        "Active Strategies:",
    ]
    for s in portfolio.active_strategies:
        marker = "⚠ OVERUSED" if s in portfolio.overused_strategies else "✓"
        lines.append(f"  {marker} {s}")
    if portfolio.overused_strategies:
        lines.append("")
        lines.append("Overused Strategies:")
        for s in portfolio.overused_strategies:
            lines.append(f"  — {s}: rotation recommended this cycle")
    return _box("Adaptation Portfolio State", lines)


def render_continuity_summary(assessment: ContinuityAssessment) -> str:
    lines = [
        f"Continuity State : {assessment.continuity_state.upper()}",
        f"Oper. Trust      : {assessment.operational_trust_level.upper()}",
        f"Resilience Outl. : {assessment.resilience_outlook.upper()}",
        "",
        "Future Recovery Capacity:",
    ]
    for i in range(0, len(assessment.future_recovery_capacity), 76):
        lines.append(f"  {assessment.future_recovery_capacity[i:i+76]}")
    lines.append("")
    lines.append("Strategic Risk:")
    for i in range(0, len(assessment.strategic_risk), 76):
        lines.append(f"  {assessment.strategic_risk[i:i+76]}")
    return _box("Organizational Continuity Summary", lines)
