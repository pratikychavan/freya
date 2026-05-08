"""Terminal-friendly rendering helpers for the Business Travel demo."""
from __future__ import annotations

from freya.events.models import RuntimeEvent
from freya.strategies.timeline import render_strategy_timeline
from freya.economics.visualization import render_execution_economics


WIDTH = 72


def header(title: str) -> str:
    bar = "═" * WIDTH
    inner = f"  {title}"
    return f"\n{bar}\n{inner}\n{bar}"


def section(title: str) -> str:
    bar = "─" * WIDTH
    return f"\n{bar}\n  {title}\n{bar}"


def divider() -> str:
    return "─" * WIDTH


def render_banner() -> str:
    lines = [
        "╔" + "═" * (WIDTH - 2) + "╗",
        "║" + " " * (WIDTH - 2) + "║",
        "║" + "  FREYA SDK — BUSINESS TRAVEL COORDINATOR DEMO".center(WIDTH - 2) + "║",
        "║" + "  Step 29: Real Governed Adaptive Workflow".center(WIDTH - 2) + "║",
        "║" + " " * (WIDTH - 2) + "║",
        "╚" + "═" * (WIDTH - 2) + "╝",
    ]
    return "\n".join(lines)


def render_request(goal: str) -> str:
    lines = [
        section("USER REQUEST"),
        "",
        f'  "{goal}"',
        "",
    ]
    return "\n".join(lines)


def render_event_stream(events: list[dict]) -> str:
    """Render a curated subset of runtime events for the demo audience."""
    _INTERESTING = {
        "execution_strategy_selected",
        "runtime_failure_observed",
        "runtime_recovery_attempted",
        "runtime_recovery_succeeded",
        "governance_evaluated",
        "workflow_paused_for_approval",
        "workflow_resumed_after_approval",
        "workflow_snapshot_persisted",
        "workflow_snapshot_restored",
        "planner_terminated",
        "workflow_completed",
        "workflow_budget_exceeded",
    }

    lines = [section("RUNTIME EVENTS"), ""]
    seen = 0
    for ev in events:
        if ev["event_type"] not in _INTERESTING:
            continue
        iter_label = f"iter={ev['iteration']}" if ev.get("iteration") is not None else "     "
        payload = ev.get("payload", {})

        if ev["event_type"] == "execution_strategy_selected":
            strat = payload.get("strategy", "?")
            reason = payload.get("reason", "")[:60]
            lines.append(f"  [{iter_label}]  strategy → {strat:<18}  {reason}")
        elif ev["event_type"] == "runtime_failure_observed":
            lines.append(f"  [{iter_label}]  ⚠  runtime failure observed")
        elif ev["event_type"] == "runtime_recovery_attempted":
            task_ids = payload.get("task_ids", [])
            lines.append(f"  [{iter_label}]  ↩  recovery attempted for: {task_ids}")
        elif ev["event_type"] == "runtime_recovery_succeeded":
            lines.append(f"  [{iter_label}]  ✓  recovery succeeded")
        elif ev["event_type"] == "governance_evaluated":
            decision = payload.get("decision", "?")
            risk = payload.get("risk_level", "")
            policies = payload.get("triggered_policies", [])
            pol_str = f"  [{', '.join(policies)}]" if policies else ""
            lines.append(f"  [{iter_label}]  ⚖  governance → {decision}{pol_str}  risk={risk or 'none'}")
        elif ev["event_type"] == "workflow_paused_for_approval":
            req_id = payload.get("request_id", "?")[:8]
            lines.append(f"  [{iter_label}]  ⏸  WORKFLOW PAUSED — request={req_id}…")
        elif ev["event_type"] == "workflow_snapshot_persisted":
            ver = payload.get("version", "?")
            lines.append(f"  [{iter_label}]  💾 snapshot saved (version={ver})")
        elif ev["event_type"] == "workflow_snapshot_restored":
            ver = payload.get("version", "?")
            lines.append(f"  [{iter_label}]  ♻  snapshot restored (version={ver})")
        elif ev["event_type"] == "workflow_resumed_after_approval":
            lines.append(f"  [{iter_label}]  ▶  WORKFLOW RESUMED after approval")
        elif ev["event_type"] == "workflow_budget_exceeded":
            fields = payload.get("exceeded_fields", [])
            lines.append(f"  [{iter_label}]  💰 budget exceeded: {fields}")
        elif ev["event_type"] == "workflow_completed":
            lines.append(f"  [{iter_label}]  ✅ workflow completed")
        elif ev["event_type"] == "planner_terminated":
            reason = payload.get("reason", "?")
            lines.append(f"  [{iter_label}]  ✅ planner terminated: {reason}")
        seen += 1

    if not seen:
        lines.append("  (no significant events recorded)")
    lines.append("")
    return "\n".join(lines)


def render_governance_section(events: list[dict]) -> str:
    """Render governance decisions and their resolutions."""
    lines = [section("GOVERNANCE DECISIONS"), ""]
    approval_events = [e for e in events if e["event_type"] == "workflow_paused_for_approval"]
    gov_events = [e for e in events if e["event_type"] == "governance_evaluated"
                  and e.get("payload", {}).get("decision") == "require_approval"]

    if not approval_events and not gov_events:
        lines.append("  No governance interventions.")
        lines.append("")
        return "\n".join(lines)

    for ev in gov_events:
        p = ev.get("payload", {})
        lines.append(f"  Decision   : REQUIRE_APPROVAL")
        lines.append(f"  Reason     : {p.get('reason', '?')}")
        lines.append(f"  Risk level : {p.get('risk_level', 'unknown')}")
        lines.append(f"  Policies   : {', '.join(p.get('triggered_policies', []))}")

    for ev in approval_events:
        p = ev.get("payload", {})
        lines.append(f"  Request ID : {p.get('request_id', '?')[:16]}…")

    resume_event = next((e for e in events if e["event_type"] == "workflow_resumed_after_approval"), None)
    if resume_event:
        lines.append(f"  Resolution : ✅ APPROVED — workflow resumed successfully")

    lines.append("")
    return "\n".join(lines)


def render_final_plan(
    selected_flight: dict,
    selected_hotel: dict,
    hotel_reasoning: str,
    itinerary: dict,
    cost_summary: dict,
    approved_over_budget: bool,
) -> str:
    lines = [header("FINAL TRIP PLAN"), ""]

    # Flight
    lines.append("  FLIGHT")
    lines.append(f"    {selected_flight.get('airline', '?')} {selected_flight.get('flight_number', '')}")
    lines.append(f"    {selected_flight.get('origin', '?')} → {selected_flight.get('destination', '?')}")
    lines.append(f"    Departure : {selected_flight.get('departure', '?')}")
    lines.append(f"    Arrival   : {selected_flight.get('arrival', '?')}")
    lines.append(f"    Cost      : ₹{selected_flight.get('price_inr', 0):,}")
    lines.append("")

    # Hotel
    hotel_cost = selected_hotel.get("price_per_night_inr", 0) * 2
    budget_flag = "  ⚠ APPROVED OVER PREFERRED BUDGET" if approved_over_budget else "  ✓ within budget"
    lines.append("  HOTEL")
    lines.append(f"    {selected_hotel.get('name', '?')}")
    lines.append(f"    Location  : {selected_hotel.get('location', '?')}")
    lines.append(f"    Rate      : ₹{selected_hotel.get('price_per_night_inr', 0):,}/night × 2 nights = ₹{hotel_cost:,}")
    lines.append(f"    Distance  : {selected_hotel.get('distance_from_venue_km', '?')} km from venue")
    lines.append(f"    Stars     : {'★' * selected_hotel.get('stars', 0)}")
    lines.append(f"    {budget_flag.strip()}")
    if hotel_reasoning:
        # Truncate for display
        short = hotel_reasoning[:180].rstrip()
        if len(hotel_reasoning) > 180:
            short += "…"
        lines.append(f"    Reasoning : {short}")
    lines.append("")

    # Itinerary
    lines.append("  MEETING ITINERARY")
    venue = itinerary.get("venue", "")
    if venue:
        lines.append(f"    Venue: {venue}")
    for day, agenda_items in itinerary.get("days", {}).items():
        lines.append(f"    {day}:")
        for item in agenda_items:
            lines.append(f"      • {item}")
    lines.append("")

    # Costs
    lines.append("  COST SUMMARY")
    lines.append(f"    Flight          : ₹{cost_summary.get('flight_cost_inr', 0):,}")
    lines.append(f"    Hotel (2 nights): ₹{cost_summary.get('hotel_cost_inr', 0):,}")
    lines.append(f"    Miscellaneous   : ₹{cost_summary.get('misc_cost_inr', 0):,}")
    lines.append(f"    {'─' * 30}")
    total = cost_summary.get("total_cost_inr", 0)
    budget = cost_summary.get("budget_inr", 40_000)
    within = cost_summary.get("within_budget", True)
    status_icon = "✓" if within else "⚠"
    lines.append(f"    TOTAL           : ₹{total:,}  {status_icon}")
    lines.append(f"    Budget          : ₹{budget:,}")
    lines.append("")

    # Status
    lines.append(f"  WORKFLOW STATUS : SUCCESS")
    lines.append("")
    return "\n".join(lines)
