from __future__ import annotations

from freya.planner.trace import PlannerTrace


def render_strategy_timeline(result: object) -> str:
    """Render a text-only strategy timeline from a PlannerResult or PlannerTrace.

    Each row shows:
        iter=N  <strategy_name>  → <outcome>

    The function inspects ``result.trace`` (if a PlannerResult is passed) or
    the trace directly (if a PlannerTrace is passed) for
    ``execution_strategy_selected`` events and pairs them with the next
    ``planner_iteration`` or ``planner_terminated`` event on the same iteration
    to determine the outcome.
    """
    # Accept either a PlannerTrace or a PlannerResult duck-typing
    trace: PlannerTrace
    if isinstance(result, PlannerTrace):
        trace = result
    else:
        trace = getattr(result, "trace", result)  # type: ignore[arg-type]

    lines: list[str] = [
        f"Strategy Timeline  session={trace.session_id[:8]}…",
        "-" * 56,
    ]

    # Index strategy-selected events by iteration
    strategy_by_iter: dict[int, dict] = {}
    for ev in trace.events:
        if ev.event_type == "execution_strategy_selected":
            strategy_by_iter[ev.iteration] = ev.payload

    # Also note escalations
    escalated_by_iter: dict[int, str] = {}
    for ev in trace.events:
        if ev.event_type == "execution_strategy_escalated":
            escalated_by_iter[ev.iteration] = ev.payload.get("escalated_to", "?")

    # Determine outcome per iteration
    def _outcome(iteration: int) -> str:
        for ev in trace.events:
            if ev.iteration != iteration:
                continue
            if ev.event_type == "planner_terminated":
                return ev.payload.get("reason", "terminated")
            if ev.event_type == "runtime_failure_terminal":
                return "runtime_failure_terminal"
            if ev.event_type == "workflow_paused_for_approval":
                return "paused_for_approval"
            if ev.event_type == "workflow_rejected_by_governance":
                return "rejected_by_governance"
        return "completed"

    if not strategy_by_iter:
        lines.append("(no strategy events recorded)")
    else:
        for iteration in sorted(strategy_by_iter):
            payload = strategy_by_iter[iteration]
            strategy = payload.get("strategy", "unknown")
            escalated = escalated_by_iter.get(iteration)
            if escalated:
                strategy_label = f"{strategy} → {escalated}"
            else:
                strategy_label = strategy
            outcome = _outcome(iteration)
            lines.append(f"  iter={iteration:<3}  {strategy_label:<28}  → {outcome}")

    lines.append("-" * 56)
    lines.append(
        f"  status={trace.status}  "
        f"iterations={trace.iterations_completed}  "
        f"reason={trace.termination_reason or 'none'}"
    )
    return "\n".join(lines)
