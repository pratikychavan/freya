"""freya/experience/rendering.py

Progressive-disclosure rendering layer.

Three view tiers:
  USER VIEW        — progress, approvals, narrative outcomes only.
  POWER USER VIEW  — economics, high-level strategy changes, summaries.
  ENGINEER VIEW    — raw events, strategies, traces, governance internals.

Observability is NEVER removed — it is layered behind view tiers.
"""
from __future__ import annotations

from typing import Any

from freya.experience.models import NarrativeSummary
from freya.experience.progress import WorkflowProgressTracker
from freya.experience.translators import RuntimeEventTranslator

# ---------------------------------------------------------------------------
# Shared layout helpers
# ---------------------------------------------------------------------------

_W = 72  # terminal width


def _rule(char: str = "─") -> str:
    return char * _W


def _header(title: str, char: str = "─") -> str:
    padding = _W - len(title) - 4
    return f"\n  {char * 2} {title} {char * max(0, padding)}\n"


def _box_title(title: str) -> str:
    inner = f"  {title}  "
    bar = "═" * len(inner)
    return f"╔{bar}╗\n║{inner}║\n╚{bar}╝"


# ---------------------------------------------------------------------------
# USER VIEW
# ---------------------------------------------------------------------------

def render_user_view(
    goal: str,
    tracker: WorkflowProgressTracker,
    narrative: NarrativeSummary | None = None,
    approval_block: str | None = None,
) -> str:
    """Render the minimal human-facing view.

    Shows: intent, progress steps, approval (if any), outcome summary.
    No runtime mechanics, no strategies, no traces.
    """
    sections: list[str] = []

    sections.append(_header("YOUR REQUEST", "─"))
    sections.append(f'  "{goal}"\n')

    sections.append(_header("PROGRESS", "─"))
    sections.append(tracker.render())

    continuity = tracker.render_continuity()
    if continuity:
        sections.append("")
        sections.append(continuity)

    if approval_block:
        sections.append(_header("ACTION REQUIRED", "─"))
        sections.append(approval_block)

    if narrative:
        sections.append(_header("YOUR TRIP PLAN", "─"))
        sections.append(narrative.render())

    return "\n".join(sections) + "\n"


# ---------------------------------------------------------------------------
# POWER USER VIEW
# ---------------------------------------------------------------------------

def render_power_user_view(
    goal: str,
    tracker: WorkflowProgressTracker,
    narrative: NarrativeSummary | None = None,
    economics: object | None = None,
    strategy_changes: list[tuple[int, str]] | None = None,
    approval_block: str | None = None,
) -> str:
    """Render the power-user view.

    Adds execution economics and high-level strategy changes on top of
    the user view. Still hides raw events and internal traces.
    """
    sections: list[str] = [render_user_view(goal, tracker, narrative, approval_block)]

    if strategy_changes:
        sections.append(_header("STRATEGY OVERVIEW", "─"))
        for iteration, strategy in strategy_changes:
            label = _strategy_label(strategy)
            sections.append(f"  iter={iteration:<3}  {label}")
        sections.append("")

    if economics is not None:
        sections.append(_header("EXECUTION ECONOMICS", "─"))
        sections.append(_render_economics_compact(economics))

    return "\n".join(sections)


def _strategy_label(strategy: str) -> str:
    labels = {
        "deterministic": "Deterministic  — fast, rule-based execution",
        "cognitive":      "Cognitive      — deep AI reasoning applied",
        "recovery":       "Recovery       — automatic failure mitigation",
        "human_approval": "Human approval — workflow paused for review",
        "delegation":     "Delegation     — task handed to sub-coordinator",
    }
    return labels.get(strategy, strategy)


def _render_economics_compact(economics: object) -> str:
    cost = economics.current_cost() if hasattr(economics, "current_cost") else None
    within = economics.within_budget() if hasattr(economics, "within_budget") else True
    budget_status = "WITHIN_LIMIT" if within else "EXCEEDED"
    if cost is None:
        return "  (no economics data)\n"
    lines = [
        f"  Total tokens used    : {cost.token_cost:,}",
        f"  AI reasoning calls   : {cost.cognitive_invocations}",
        f"  Recovery attempts    : {cost.recovery_attempts}",
        f"  Estimated cost       : ${cost.estimated_monetary_cost:.2f}",
        f"  Budget status        : {budget_status}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# ENGINEER VIEW
# ---------------------------------------------------------------------------

def render_engineer_view(
    goal: str,
    all_events: list[dict],
    economics: object | None = None,
    strategy_timeline_str: str | None = None,
    workflow_tree_str: str | None = None,
    governance_events: list[dict] | None = None,
) -> str:
    """Render the full engineer-facing view.

    Shows everything: raw events, strategies, economics, workflow tree,
    governance internals. No information is hidden.
    """
    sections: list[str] = []

    sections.append(_header("ENGINEER VIEW — FULL OBSERVABILITY", "═"))
    sections.append(f'  Goal: "{goal}"\n')

    if workflow_tree_str:
        sections.append(_header("WORKFLOW TREE", "─"))
        for line in workflow_tree_str.splitlines():
            sections.append(f"  {line}")
        sections.append("")

    sections.append(_header("RAW RUNTIME EVENTS", "─"))
    if all_events:
        sections.append(_render_raw_events(all_events))
    else:
        sections.append("  (no events recorded)\n")

    if governance_events:
        sections.append(_header("GOVERNANCE INTERNALS", "─"))
        sections.append(_render_governance(governance_events))

    if strategy_timeline_str:
        sections.append(_header("STRATEGY TIMELINE", "─"))
        for line in strategy_timeline_str.splitlines():
            sections.append(f"  {line}")
        sections.append("")

    if economics is not None:
        sections.append(_header("EXECUTION ECONOMICS — FULL", "─"))
        sections.append(_render_economics_full(economics))

    return "\n".join(sections)


def _render_raw_events(events: list[dict]) -> str:
    lines: list[str] = []
    for ev in events:
        etype = ev.get("event_type", "")
        iteration = ev.get("iteration")
        payload = ev.get("payload", {})
        iter_str = f"iter={iteration}" if iteration is not None else "     "
        # Show one key payload field if present
        detail = _payload_hint(etype, payload)
        lines.append(f"  [{iter_str}]  {etype:<44}  {detail}")
    return "\n".join(lines) + "\n"


def _payload_hint(event_type: str, payload: dict) -> str:
    if event_type == "execution_strategy_selected":
        return f"strategy={payload.get('strategy', '?')}"
    if event_type in ("tool_call_started", "tool_call_completed"):
        return f"tool={payload.get('tool_name', '?')}"
    if event_type == "governance_evaluated":
        return f"decision={payload.get('decision', '?')}"
    if event_type == "runtime_failure_observed":
        return f"task={payload.get('task_id', '?')}"
    if event_type == "execution_cost_recorded":
        return f"tokens={payload.get('token_cost', '?')}"
    return ""


def _render_governance(events: list[dict]) -> str:
    gov_events = [
        e for e in events
        if e.get("event_type", "").startswith("governance")
        or e.get("event_type", "") in (
            "workflow_paused_for_approval",
            "workflow_resumed_after_approval",
            "workflow_rejected_by_governance",
        )
    ]
    if not gov_events:
        return "  (no governance events)\n"
    lines: list[str] = []
    for ev in gov_events:
        p = ev.get("payload", {})
        lines.append(
            f"  [{ev.get('event_type')}]  "
            f"decision={p.get('decision', p.get('state', '?'))}  "
            f"risk={p.get('risk_level', 'none')}"
        )
    return "\n".join(lines) + "\n"


def _render_economics_full(economics: object) -> str:
    cost = economics.current_cost() if hasattr(economics, "current_cost") else None
    within = economics.within_budget() if hasattr(economics, "within_budget") else True
    priority = economics._priority.value if hasattr(economics, "_priority") else "normal"
    history = economics.strategy_history() if hasattr(economics, "strategy_history") else []
    budget_status = "WITHIN_LIMIT" if within else "EXCEEDED"
    if cost is None:
        return "  (no economics data)\n"
    lines = [
        f"  Total token cost       : {cost.token_cost:,}",
        f"  Runtime seconds        : {cost.runtime_seconds:.2f}",
        f"  Cognitive invocations  : {cost.cognitive_invocations}",
        f"  Delegations            : {cost.delegation_count}",
        f"  Recovery attempts      : {cost.recovery_attempts}",
        f"  Approval requests      : {cost.approval_requests}",
        f"  Estimated cost USD     : ${cost.estimated_monetary_cost:.4f}",
        f"  Priority               : {priority}",
        f"  Budget status          : {budget_status}",
    ]
    if history:
        totals: dict[str, int] = {}
        for entry in history:
            strat = entry.get("strategy", "unknown")
            tokens = entry.get("cost", {}).get("token_cost", 0)
            totals[strat] = totals.get(strat, 0) + tokens
        lines.append("")
        lines.append("  Strategy cost breakdown:")
        for strat, tokens in totals.items():
            lines.append(f"    {strat:<20}: {tokens} tokens")
    return "\n".join(lines) + "\n"
