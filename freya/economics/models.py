from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class WorkflowPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionCost(BaseModel):
    """Accumulated execution cost for a single workflow run."""

    token_cost: int = 0
    runtime_seconds: float = 0.0
    cognitive_invocations: int = 0
    delegation_count: int = 0
    recovery_attempts: int = 0
    approval_requests: int = 0
    estimated_monetary_cost: float = 0.0

    def add(self, other: "ExecutionCost") -> "ExecutionCost":
        """Return a new ExecutionCost that is the sum of self and other."""
        return ExecutionCost(
            token_cost=self.token_cost + other.token_cost,
            runtime_seconds=self.runtime_seconds + other.runtime_seconds,
            cognitive_invocations=self.cognitive_invocations + other.cognitive_invocations,
            delegation_count=self.delegation_count + other.delegation_count,
            recovery_attempts=self.recovery_attempts + other.recovery_attempts,
            approval_requests=self.approval_requests + other.approval_requests,
            estimated_monetary_cost=self.estimated_monetary_cost + other.estimated_monetary_cost,
        )


class WorkflowBudget(BaseModel):
    """Hard and soft resource limits for a workflow execution."""

    max_token_cost: int | None = None
    max_runtime_seconds: float | None = None
    max_cognitive_invocations: int | None = None
    max_delegations: int | None = None
    max_recovery_attempts: int | None = None
    max_approval_requests: int | None = None
    max_estimated_cost: float | None = None

    def within_budget(self, cost: ExecutionCost) -> bool:
        """Return True if *cost* does not exceed any configured limit."""
        checks = [
            (self.max_token_cost, cost.token_cost),
            (self.max_runtime_seconds, cost.runtime_seconds),
            (self.max_cognitive_invocations, cost.cognitive_invocations),
            (self.max_delegations, cost.delegation_count),
            (self.max_recovery_attempts, cost.recovery_attempts),
            (self.max_approval_requests, cost.approval_requests),
            (self.max_estimated_cost, cost.estimated_monetary_cost),
        ]
        for limit, actual in checks:
            if limit is not None and actual > limit:
                return False
        return True

    def exceeded_fields(self, cost: ExecutionCost) -> list[str]:
        """Return names of all budget fields that have been exceeded."""
        mapping = [
            ("max_token_cost", self.max_token_cost, cost.token_cost),
            ("max_runtime_seconds", self.max_runtime_seconds, cost.runtime_seconds),
            ("max_cognitive_invocations", self.max_cognitive_invocations, cost.cognitive_invocations),
            ("max_delegations", self.max_delegations, cost.delegation_count),
            ("max_recovery_attempts", self.max_recovery_attempts, cost.recovery_attempts),
            ("max_approval_requests", self.max_approval_requests, cost.approval_requests),
            ("max_estimated_cost", self.max_estimated_cost, cost.estimated_monetary_cost),
        ]
        return [name for name, limit, actual in mapping if limit is not None and actual > limit]
