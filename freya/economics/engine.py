from __future__ import annotations

from freya.economics.models import ExecutionCost, WorkflowBudget, WorkflowPriority
from freya.strategies.models import ExecutionStrategy

# ---------------------------------------------------------------------------
# Deterministic per-strategy cost table
# ---------------------------------------------------------------------------
_STRATEGY_COST_TABLE: dict[str, ExecutionCost] = {
    ExecutionStrategy.DETERMINISTIC.value: ExecutionCost(
        token_cost=10,
        runtime_seconds=0.5,
        estimated_monetary_cost=0.01,
    ),
    ExecutionStrategy.REPAIR.value: ExecutionCost(
        token_cost=80,
        runtime_seconds=1.5,
        estimated_monetary_cost=0.08,
    ),
    ExecutionStrategy.RECOVERY.value: ExecutionCost(
        token_cost=50,
        runtime_seconds=2.0,
        recovery_attempts=1,
        estimated_monetary_cost=0.05,
    ),
    ExecutionStrategy.COGNITIVE.value: ExecutionCost(
        token_cost=250,
        runtime_seconds=3.0,
        cognitive_invocations=1,
        estimated_monetary_cost=0.25,
    ),
    ExecutionStrategy.DELEGATION.value: ExecutionCost(
        token_cost=400,
        runtime_seconds=5.0,
        delegation_count=1,
        estimated_monetary_cost=0.40,
    ),
    ExecutionStrategy.HUMAN_APPROVAL.value: ExecutionCost(
        token_cost=5,
        runtime_seconds=0.1,
        approval_requests=1,
        estimated_monetary_cost=15.0,
    ),
    ExecutionStrategy.TERMINATE.value: ExecutionCost(
        token_cost=0,
        runtime_seconds=0.0,
        estimated_monetary_cost=0.0,
    ),
}

# Priority-based soft-limit multipliers (>1 = more headroom)
_PRIORITY_MULTIPLIER: dict[str, float] = {
    WorkflowPriority.LOW.value: 0.5,
    WorkflowPriority.NORMAL.value: 1.0,
    WorkflowPriority.HIGH.value: 2.0,
    WorkflowPriority.CRITICAL.value: float("inf"),  # no soft limit
}


class ExecutionEconomicsEngine:
    """Tracks accumulated execution cost, evaluates budgets, and estimates strategy costs.

    All cost estimates are deterministic (table-driven, no ML/randomness).
    """

    def __init__(
        self,
        budget: WorkflowBudget | None = None,
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
    ) -> None:
        self._budget = budget or WorkflowBudget()
        self._priority = priority
        self._accumulated = ExecutionCost()
        self._strategy_history: list[dict] = []

    # ------------------------------------------------------------------
    # Accumulation
    # ------------------------------------------------------------------

    def record_cost(self, cost: ExecutionCost, strategy: str | None = None) -> None:
        """Add *cost* to the running total and optionally note the strategy."""
        self._accumulated = self._accumulated.add(cost)
        if strategy is not None:
            self._strategy_history.append({
                "strategy": strategy,
                "cost": cost.model_dump(),
                "cumulative": self._accumulated.model_dump(),
            })

    def record_strategy(self, strategy: ExecutionStrategy) -> None:
        """Record the estimated cost for *strategy* automatically."""
        cost = self.strategy_cost_estimate(strategy)
        self.record_cost(cost, strategy=strategy.value)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def current_cost(self) -> ExecutionCost:
        return self._accumulated

    def strategy_history(self) -> list[dict]:
        return list(self._strategy_history)

    def within_budget(self) -> bool:
        """Return True if accumulated cost has NOT exceeded the budget."""
        if self._priority == WorkflowPriority.CRITICAL:
            return True  # critical workflows always continue
        return self._budget.within_budget(self._accumulated)

    def exceeded_fields(self) -> list[str]:
        return self._budget.exceeded_fields(self._accumulated)

    def remaining_budget(self) -> WorkflowBudget:
        """Return a WorkflowBudget representing how much headroom is left.

        For CRITICAL priority all limits are None (unlimited).
        """
        if self._priority == WorkflowPriority.CRITICAL:
            return WorkflowBudget()

        mult = _PRIORITY_MULTIPLIER.get(self._priority.value, 1.0)
        cost = self._accumulated

        def _remaining(limit: float | int | None, actual: float) -> float | int | None:
            if limit is None:
                return None
            effective = limit * mult
            r = effective - actual
            return max(0, round(r, 6))

        return WorkflowBudget(
            max_token_cost=_remaining(self._budget.max_token_cost, cost.token_cost),
            max_runtime_seconds=_remaining(self._budget.max_runtime_seconds, cost.runtime_seconds),
            max_cognitive_invocations=_remaining(
                self._budget.max_cognitive_invocations, cost.cognitive_invocations
            ),
            max_delegations=_remaining(self._budget.max_delegations, cost.delegation_count),
            max_recovery_attempts=_remaining(
                self._budget.max_recovery_attempts, cost.recovery_attempts
            ),
            max_approval_requests=_remaining(
                self._budget.max_approval_requests, cost.approval_requests
            ),
            max_estimated_cost=_remaining(
                self._budget.max_estimated_cost, cost.estimated_monetary_cost
            ),
        )

    # ------------------------------------------------------------------
    # Estimation
    # ------------------------------------------------------------------

    def strategy_cost_estimate(self, strategy: ExecutionStrategy) -> ExecutionCost:
        """Return the deterministic cost estimate for *strategy*."""
        return _STRATEGY_COST_TABLE.get(strategy.value, ExecutionCost())

    def would_exceed_budget(self, strategy: ExecutionStrategy) -> bool:
        """Return True if executing *strategy* once would exceed the budget."""
        if self._priority == WorkflowPriority.CRITICAL:
            return False
        projected = self._accumulated.add(self.strategy_cost_estimate(strategy))
        mult = _PRIORITY_MULTIPLIER.get(self._priority.value, 1.0)

        budget = self._budget
        checks: list[tuple[float | int | None, float]] = [
            (budget.max_token_cost, projected.token_cost),
            (budget.max_runtime_seconds, projected.runtime_seconds),
            (budget.max_cognitive_invocations, projected.cognitive_invocations),
            (budget.max_delegations, projected.delegation_count),
            (budget.max_recovery_attempts, projected.recovery_attempts),
            (budget.max_approval_requests, projected.approval_requests),
            (budget.max_estimated_cost, projected.estimated_monetary_cost),
        ]
        for limit, actual in checks:
            if limit is not None and actual > limit * mult:
                return True
        return False

    # ------------------------------------------------------------------
    # Serialization (for snapshot persistence)
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "accumulated_cost": self._accumulated.model_dump(),
            "budget": self._budget.model_dump(),
            "priority": self._priority.value,
            "strategy_history": self._strategy_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionEconomicsEngine":
        engine = cls(
            budget=WorkflowBudget(**data.get("budget", {})),
            priority=WorkflowPriority(data.get("priority", "normal")),
        )
        engine._accumulated = ExecutionCost(**data.get("accumulated_cost", {}))
        engine._strategy_history = list(data.get("strategy_history", []))
        return engine
