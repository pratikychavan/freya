from __future__ import annotations

from freya.strategies.models import ExecutionStrategy, StrategyDecision
from freya.strategies.signals import RuntimeSignals


class ExecutionStrategyEngine:
    """Selects the next execution strategy from observable runtime signals.

    Strategy precedence (evaluated in order):
    1. TERMINATE   — unrecoverable failures exceed threshold
    2. HUMAN_APPROVAL — governance block pending or forced HITL
    3. RECOVERY    — runtime failures present, within retry limit
    4. REPAIR      — validation failures present, within repair limit
    5. COGNITIVE   — confidence_score signals planner needs reasoning
    6. DELEGATION  — explicit delegation signals present
    7. DETERMINISTIC — default safe path

    The engine is:
    - deterministic (no randomness)
    - explainable  (every decision carries a reason)
    - inspectable  (returns a StrategyDecision with full payload)
    """

    def __init__(
        self,
        max_recovery_attempts: int = 2,
        max_validation_failures: int = 1,
        max_governance_blocks: int = 3,
        cognitive_confidence_threshold: float = 0.5,
    ) -> None:
        self._max_recovery = max_recovery_attempts
        self._max_validation = max_validation_failures
        self._max_governance = max_governance_blocks
        self._cognitive_threshold = cognitive_confidence_threshold

    def select_strategy(
        self,
        planning_context: object,
        workflow_state: object,
        runtime_signals: RuntimeSignals,
    ) -> StrategyDecision:
        """Evaluate signals and return the recommended StrategyDecision."""
        triggered: list[str] = []

        # ── 1. Terminate if unrecoverable ──────────────────────────────────
        if runtime_signals.recovery_attempts > self._max_recovery:
            triggered.append("max_recovery_attempts_exceeded")
            return StrategyDecision(
                strategy=ExecutionStrategy.TERMINATE,
                reason=(
                    f"Recovery attempts ({runtime_signals.recovery_attempts}) "
                    f"exceed limit ({self._max_recovery}). Workflow unrecoverable."
                ),
                confidence=1.0,
                triggered_by=triggered,
            )

        # ── 2. Human approval if governance blocked or pending approvals ────
        if runtime_signals.pending_approvals > 0:
            triggered.append("pending_approvals")
            return StrategyDecision(
                strategy=ExecutionStrategy.HUMAN_APPROVAL,
                reason=(
                    f"{runtime_signals.pending_approvals} approval(s) pending. "
                    "Execution paused for human review."
                ),
                confidence=1.0,
                triggered_by=triggered,
            )
        if runtime_signals.governance_blocks >= self._max_governance:
            triggered.append("repeated_governance_blocks")
            return StrategyDecision(
                strategy=ExecutionStrategy.HUMAN_APPROVAL,
                reason=(
                    f"Repeated governance blocks ({runtime_signals.governance_blocks}). "
                    "Forcing human approval."
                ),
                confidence=0.9,
                triggered_by=triggered,
            )

        # ── 3. Recovery if runtime failures within retry limit ──────────────
        if runtime_signals.runtime_failures > 0:
            triggered.append("runtime_failures_present")
            return StrategyDecision(
                strategy=ExecutionStrategy.RECOVERY,
                reason=(
                    f"{runtime_signals.runtime_failures} runtime failure(s) observed. "
                    "Attempting recovery strategy."
                ),
                confidence=0.85,
                triggered_by=triggered,
            )

        # ── 4. Repair if validation failures within limit ───────────────────
        if runtime_signals.validation_failures > 0:
            triggered.append("validation_failures_present")
            return StrategyDecision(
                strategy=ExecutionStrategy.REPAIR,
                reason=(
                    f"{runtime_signals.validation_failures} validation failure(s). "
                    "Switching to repair strategy."
                ),
                confidence=0.85,
                triggered_by=triggered,
            )

        # ── 5. Cognitive if confidence below threshold ──────────────────────
        if (
            runtime_signals.confidence_score is not None
            and runtime_signals.confidence_score < self._cognitive_threshold
        ):
            triggered.append("low_confidence_score")
            return StrategyDecision(
                strategy=ExecutionStrategy.COGNITIVE,
                reason=(
                    f"Confidence score {runtime_signals.confidence_score:.2f} "
                    f"below threshold {self._cognitive_threshold:.2f}. "
                    "Escalating to cognitive strategy."
                ),
                confidence=0.8,
                triggered_by=triggered,
            )

        # ── 6. Delegation if delegation failures should trigger rerouting ───
        if runtime_signals.delegation_failures > 0:
            triggered.append("delegation_failures_present")
            return StrategyDecision(
                strategy=ExecutionStrategy.DELEGATION,
                reason=(
                    f"{runtime_signals.delegation_failures} delegation failure(s) observed. "
                    "Re-evaluating delegation strategy."
                ),
                confidence=0.75,
                triggered_by=triggered,
            )

        # ── 7. Default: deterministic ───────────────────────────────────────
        return StrategyDecision(
            strategy=ExecutionStrategy.DETERMINISTIC,
            reason="No escalation signals. Continuing with deterministic execution.",
            confidence=1.0,
            triggered_by=[],
        )
