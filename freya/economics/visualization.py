from __future__ import annotations

from freya.economics.engine import ExecutionEconomicsEngine
from freya.economics.models import ExecutionCost, WorkflowBudget


def render_execution_economics(
    engine: ExecutionEconomicsEngine | None = None,
    *,
    cost: ExecutionCost | None = None,
    budget: WorkflowBudget | None = None,
) -> str:
    """Render a text-only execution economics summary.

    Pass either an ``ExecutionEconomicsEngine`` instance (preferred) or
    individual ``cost`` / ``budget`` objects.
    """
    if engine is not None:
        cost = engine.current_cost()
        budget_obj = engine._budget
        priority = engine._priority.value
        history = engine.strategy_history()
        within = engine.within_budget()
    else:
        cost = cost or ExecutionCost()
        budget_obj = budget or WorkflowBudget()
        priority = "normal"
        history = []
        within = budget_obj.within_budget(cost)

    budget_status = "WITHIN_LIMIT" if within else "EXCEEDED"

    lines: list[str] = [
        "Execution Economics Report",
        "─" * 48,
        f"  Total token cost       : {cost.token_cost}",
        f"  Runtime seconds        : {cost.runtime_seconds:.2f}",
        f"  Cognitive invocations  : {cost.cognitive_invocations}",
        f"  Delegations            : {cost.delegation_count}",
        f"  Recovery attempts      : {cost.recovery_attempts}",
        f"  Approval requests      : {cost.approval_requests}",
        f"  Estimated cost         : ${cost.estimated_monetary_cost:.2f}",
        f"  Priority               : {priority}",
        f"  Budget status          : {budget_status}",
    ]

    # Budget limits (if configured)
    has_limits = any([
        budget_obj.max_token_cost,
        budget_obj.max_runtime_seconds,
        budget_obj.max_cognitive_invocations,
        budget_obj.max_delegations,
        budget_obj.max_recovery_attempts,
        budget_obj.max_approval_requests,
        budget_obj.max_estimated_cost,
    ])
    if has_limits:
        lines.append("")
        lines.append("  Budget limits:")
        if budget_obj.max_token_cost is not None:
            lines.append(f"    max_token_cost           : {budget_obj.max_token_cost}")
        if budget_obj.max_runtime_seconds is not None:
            lines.append(f"    max_runtime_seconds      : {budget_obj.max_runtime_seconds}")
        if budget_obj.max_cognitive_invocations is not None:
            lines.append(f"    max_cognitive_invocations: {budget_obj.max_cognitive_invocations}")
        if budget_obj.max_delegations is not None:
            lines.append(f"    max_delegations          : {budget_obj.max_delegations}")
        if budget_obj.max_recovery_attempts is not None:
            lines.append(f"    max_recovery_attempts    : {budget_obj.max_recovery_attempts}")
        if budget_obj.max_approval_requests is not None:
            lines.append(f"    max_approval_requests    : {budget_obj.max_approval_requests}")
        if budget_obj.max_estimated_cost is not None:
            lines.append(f"    max_estimated_cost       : ${budget_obj.max_estimated_cost:.2f}")

    # Strategy cost breakdown
    if history:
        lines.append("")
        lines.append("  Strategy cost breakdown:")
        totals: dict[str, int] = {}
        for entry in history:
            strat = entry.get("strategy", "unknown")
            tokens = entry.get("cost", {}).get("token_cost", 0)
            totals[strat] = totals.get(strat, 0) + tokens
        for strat, tokens in totals.items():
            lines.append(f"    {strat:<20} : {tokens} tokens")

    lines.append("─" * 48)
    return "\n".join(lines)
