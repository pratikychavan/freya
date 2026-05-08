from __future__ import annotations

import logging

from freya.governance.base import InterventionPolicy
from freya.governance.models import GovernanceDecision, InterventionDecision

logger = logging.getLogger(__name__)


class GovernanceEngine:
    """Evaluates a set of registered InterventionPolicy instances against a
    proposed DAG fragment and aggregates their decisions.

    Aggregation rules (in priority order):
      1. Any REJECT      → final REJECT
      2. Any REQUIRE_APPROVAL → final REQUIRE_APPROVAL
      3. Otherwise       → APPROVE
    """

    def __init__(self) -> None:
        self._policies: list[InterventionPolicy] = []

    def register(self, policy: InterventionPolicy) -> None:
        self._policies.append(policy)

    def evaluate(
        self,
        planning_context: object,
        proposed_dag: object,
    ) -> GovernanceDecision:
        if not self._policies:
            return GovernanceDecision(
                decision=InterventionDecision.APPROVE,
                reason="No policies registered.",
            )

        triggered: list[str] = []
        rejections: list[GovernanceDecision] = []
        approvals_required: list[GovernanceDecision] = []

        for policy in self._policies:
            name = type(policy).__name__
            try:
                result = policy.evaluate(planning_context, proposed_dag)
            except Exception as exc:
                logger.warning("Policy %s raised during evaluation: %s", name, exc)
                continue

            if result.decision == InterventionDecision.REJECT:
                triggered.append(name)
                rejections.append(result)
            elif result.decision == InterventionDecision.REQUIRE_APPROVAL:
                triggered.append(name)
                approvals_required.append(result)

        if rejections:
            first = rejections[0]
            return GovernanceDecision(
                decision=InterventionDecision.REJECT,
                reason=first.reason,
                risk_level=first.risk_level,
                triggered_policies=triggered,
            )

        if approvals_required:
            first = approvals_required[0]
            reasons = " | ".join(d.reason for d in approvals_required)
            return GovernanceDecision(
                decision=InterventionDecision.REQUIRE_APPROVAL,
                reason=reasons,
                risk_level=first.risk_level,
                triggered_policies=triggered,
            )

        return GovernanceDecision(
            decision=InterventionDecision.APPROVE,
            reason="All policies approved.",
            triggered_policies=[],
        )
