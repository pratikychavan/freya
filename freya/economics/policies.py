from __future__ import annotations

from abc import ABC, abstractmethod

from freya.economics.models import ExecutionCost, WorkflowBudget, WorkflowPriority
from freya.strategies.models import ExecutionStrategy, StrategyDecision


class EconomicPolicy(ABC):
    """Base class for budget-aware execution policies."""

    @abstractmethod
    def evaluate(
        self,
        current_cost: ExecutionCost,
        budget: WorkflowBudget,
        proposed_strategy: ExecutionStrategy,
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
    ) -> StrategyDecision | None:
        """Return a StrategyDecision override if this policy fires, else None."""


class CognitiveBudgetPolicy(EconomicPolicy):
    """Blocks cognitive escalation when the cognitive invocation budget is exhausted."""

    def __init__(self, max_cognitive_invocations: int = 3) -> None:
        self.max_cognitive = max_cognitive_invocations

    def evaluate(
        self,
        current_cost: ExecutionCost,
        budget: WorkflowBudget,
        proposed_strategy: ExecutionStrategy,
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
    ) -> StrategyDecision | None:
        if priority == WorkflowPriority.CRITICAL:
            return None
        limit = (
            budget.max_cognitive_invocations
            if budget.max_cognitive_invocations is not None
            else self.max_cognitive
        )
        if (
            proposed_strategy == ExecutionStrategy.COGNITIVE
            and current_cost.cognitive_invocations >= limit
        ):
            return StrategyDecision(
                strategy=ExecutionStrategy.HUMAN_APPROVAL,
                reason=(
                    f"CognitiveBudgetPolicy: cognitive invocations "
                    f"({current_cost.cognitive_invocations}) ≥ limit ({limit}). "
                    "Cannot escalate to cognitive — forcing human approval."
                ),
                confidence=1.0,
                triggered_by=["cognitive_budget_exhausted"],
                governance_constraints=["block_cognitive_escalation"],
            )
        return None


class DelegationCostPolicy(EconomicPolicy):
    """Blocks delegation when delegation budget is exhausted."""

    def __init__(self, max_delegations: int = 5) -> None:
        self.max_delegations = max_delegations

    def evaluate(
        self,
        current_cost: ExecutionCost,
        budget: WorkflowBudget,
        proposed_strategy: ExecutionStrategy,
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
    ) -> StrategyDecision | None:
        if priority == WorkflowPriority.CRITICAL:
            return None
        limit = (
            budget.max_delegations
            if budget.max_delegations is not None
            else self.max_delegations
        )
        if (
            proposed_strategy == ExecutionStrategy.DELEGATION
            and current_cost.delegation_count >= limit
        ):
            return StrategyDecision(
                strategy=ExecutionStrategy.TERMINATE,
                reason=(
                    f"DelegationCostPolicy: delegation count "
                    f"({current_cost.delegation_count}) ≥ limit ({limit}). "
                    "Blocking further delegation."
                ),
                confidence=1.0,
                triggered_by=["delegation_budget_exhausted"],
                governance_constraints=["block_delegation"],
            )
        return None


class RecoveryCostPolicy(EconomicPolicy):
    """Terminates runaway recovery loops that exceed the recovery budget."""

    def __init__(self, max_recovery_cost_usd: float = 5.0) -> None:
        self.max_recovery_cost = max_recovery_cost_usd

    def evaluate(
        self,
        current_cost: ExecutionCost,
        budget: WorkflowBudget,
        proposed_strategy: ExecutionStrategy,
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
    ) -> StrategyDecision | None:
        if priority == WorkflowPriority.CRITICAL:
            return None
        effective_limit = (
            budget.max_recovery_attempts
            if budget.max_recovery_attempts is not None
            else float("inf")
        )
        if (
            proposed_strategy == ExecutionStrategy.RECOVERY
            and current_cost.recovery_attempts >= effective_limit
        ):
            return StrategyDecision(
                strategy=ExecutionStrategy.TERMINATE,
                reason=(
                    f"RecoveryCostPolicy: recovery attempts "
                    f"({current_cost.recovery_attempts}) ≥ budget limit "
                    f"({effective_limit}). Terminating runaway recovery."
                ),
                confidence=1.0,
                triggered_by=["recovery_budget_exhausted"],
                governance_constraints=["halt_recovery_loop"],
            )
        return None


class HighCostApprovalPolicy(EconomicPolicy):
    """Requires HITL when estimated monetary cost exceeds a threshold."""

    def __init__(self, cost_threshold_usd: float = 50.0) -> None:
        self.threshold = cost_threshold_usd

    def evaluate(
        self,
        current_cost: ExecutionCost,
        budget: WorkflowBudget,
        proposed_strategy: ExecutionStrategy,
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
    ) -> StrategyDecision | None:
        if priority == WorkflowPriority.CRITICAL:
            return None
        if current_cost.estimated_monetary_cost >= self.threshold:
            return StrategyDecision(
                strategy=ExecutionStrategy.HUMAN_APPROVAL,
                reason=(
                    f"HighCostApprovalPolicy: estimated cost "
                    f"${current_cost.estimated_monetary_cost:.2f} ≥ "
                    f"threshold ${self.threshold:.2f}. Requiring human approval."
                ),
                confidence=1.0,
                triggered_by=["high_cost_threshold_exceeded"],
                governance_constraints=["require_human_sign_off"],
            )
        return None
