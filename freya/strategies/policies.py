from __future__ import annotations

from abc import ABC, abstractmethod

from freya.strategies.models import ExecutionStrategy, StrategyDecision
from freya.strategies.signals import RuntimeSignals


class StrategyPolicy(ABC):
    """Base class for strategy transition policies."""

    @abstractmethod
    def evaluate(
        self, signals: RuntimeSignals, current_strategy: ExecutionStrategy
    ) -> StrategyDecision | None:
        """Return a StrategyDecision if the policy fires, otherwise None."""


class MaxRecoveryAttemptsPolicy(StrategyPolicy):
    """Blocks endless recovery loops by terminating after *max_attempts*."""

    def __init__(self, max_attempts: int = 2) -> None:
        self.max_attempts = max_attempts

    def evaluate(
        self, signals: RuntimeSignals, current_strategy: ExecutionStrategy
    ) -> StrategyDecision | None:
        if signals.recovery_attempts > self.max_attempts:
            return StrategyDecision(
                strategy=ExecutionStrategy.TERMINATE,
                reason=(
                    f"MaxRecoveryAttemptsPolicy: recovery attempts "
                    f"({signals.recovery_attempts}) exceed limit ({self.max_attempts})."
                ),
                confidence=1.0,
                triggered_by=["max_recovery_attempts_policy"],
                governance_constraints=["no_further_recovery"],
            )
        return None


class CognitiveEscalationPolicy(StrategyPolicy):
    """Allows promotion from deterministic → cognitive on repeated validation failures."""

    def __init__(self, validation_failure_threshold: int = 2) -> None:
        self.threshold = validation_failure_threshold

    def evaluate(
        self, signals: RuntimeSignals, current_strategy: ExecutionStrategy
    ) -> StrategyDecision | None:
        if (
            current_strategy == ExecutionStrategy.DETERMINISTIC
            and signals.validation_failures >= self.threshold
        ):
            return StrategyDecision(
                strategy=ExecutionStrategy.COGNITIVE,
                reason=(
                    f"CognitiveEscalationPolicy: {signals.validation_failures} validation "
                    f"failures (threshold={self.threshold}). Escalating to cognitive."
                ),
                confidence=0.8,
                triggered_by=["cognitive_escalation_policy"],
                governance_constraints=["require_confidence_score"],
            )
        return None


class ForcedHumanApprovalPolicy(StrategyPolicy):
    """Forces human-approval strategy after repeated accumulated failures."""

    def __init__(self, failure_threshold: int = 3) -> None:
        self.threshold = failure_threshold

    def evaluate(
        self, signals: RuntimeSignals, current_strategy: ExecutionStrategy
    ) -> StrategyDecision | None:
        total = (
            signals.validation_failures
            + signals.runtime_failures
            + signals.governance_blocks
        )
        if total >= self.threshold:
            return StrategyDecision(
                strategy=ExecutionStrategy.HUMAN_APPROVAL,
                reason=(
                    f"ForcedHumanApprovalPolicy: total failures ({total}) "
                    f"≥ threshold ({self.threshold}). Forcing human approval."
                ),
                confidence=1.0,
                triggered_by=["forced_human_approval_policy"],
                governance_constraints=["require_human_sign_off"],
            )
        return None


class TerminationEscalationPolicy(StrategyPolicy):
    """Terminates unrecoverable workflows when total failures exceed *max_total_failures*."""

    def __init__(self, max_total_failures: int = 5) -> None:
        self.max_total = max_total_failures

    def evaluate(
        self, signals: RuntimeSignals, current_strategy: ExecutionStrategy
    ) -> StrategyDecision | None:
        total = (
            signals.validation_failures
            + signals.runtime_failures
            + signals.governance_blocks
            + signals.delegation_failures
        )
        if total >= self.max_total:
            return StrategyDecision(
                strategy=ExecutionStrategy.TERMINATE,
                reason=(
                    f"TerminationEscalationPolicy: total cumulative failures ({total}) "
                    f"≥ limit ({self.max_total}). Workflow terminated."
                ),
                confidence=1.0,
                triggered_by=["termination_escalation_policy"],
                governance_constraints=["halt_execution", "prevent_restart"],
            )
        return None
