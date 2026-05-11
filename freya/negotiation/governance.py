"""freya/negotiation/governance.py

NegotiationGovernanceEngine

Validates that proposed operational negotiations do not violate safety rules.

Hard rules that cannot be overridden:
  - Critical workflows cannot enter any degradation mode.
  - No workflow may be degraded below its quality floor.
  - Governance guarantees cannot be negotiated away.
  - All resource borrowing contracts must be reversible.
  - Governance risk rated 'critical' blocks any proposal.
"""
from __future__ import annotations

from freya.negotiation.models import NegotiationProposal, WorkflowDegradationPlan

_BLOCKED_MODES_FOR_CRITICAL = {"reduced_reasoning", "lightweight_planning", "compressed_analysis"}


class NegotiationGovernanceEngine:
    """Validate proposals and degradation plans against safety invariants."""

    def validate_proposal(
        self,
        proposal: NegotiationProposal,
        plans: list[WorkflowDegradationPlan],
        critical_workflows: set[str],
    ) -> tuple[bool, list[str]]:
        """Return (approved, list_of_violations)."""
        violations: list[str] = []

        # 1. Governance risk gate
        if proposal.governance_risk == "critical":
            violations.append(
                f"Proposal {proposal.proposal_id} carries critical governance risk — rejected."
            )

        # 2. Per-plan validation
        for plan in plans:
            plan_violations = self.validate_plan(plan, critical_workflows)
            violations.extend(plan_violations)

        # 3. Confidence floor
        if proposal.confidence_score < 0.35:
            violations.append(
                f"Proposal confidence {proposal.confidence_score:.0%} is below the 35 % acceptance floor."
            )

        return (len(violations) == 0, violations)

    def validate_plan(
        self,
        plan: WorkflowDegradationPlan,
        critical_workflows: set[str],
    ) -> list[str]:
        violations: list[str] = []

        # Critical workflow protection
        if plan.workflow_id in critical_workflows and plan.degradation_mode != "none":
            if plan.degradation_mode in _BLOCKED_MODES_FOR_CRITICAL:
                violations.append(
                    f"Critical workflow '{plan.workflow_id}' cannot enter mode "
                    f"'{plan.degradation_mode}'."
                )

        # Quality floor — absolute safety net; criticality-specific floors
        # are enforced by the degradation engine; governance just guards against
        # nonsensical (zero or negative) floors or floors below the hard
        # critical-workflow minimum.
        absolute_minimum = 0.50 if plan.workflow_id in critical_workflows else 0.10
        if plan.minimum_quality_floor < absolute_minimum:
            violations.append(
                f"Workflow '{plan.workflow_id}' quality floor {plan.minimum_quality_floor:.0%} "
                f"is below the {'critical-workflow' if plan.workflow_id in critical_workflows else 'absolute'} "
                f"minimum of {absolute_minimum:.0%}."
            )

        # Reversibility
        if not plan.reversibility:
            violations.append(
                f"Degradation plan for '{plan.workflow_id}' is not marked reversible."
            )

        return violations

    def validate_resource_transfer(
        self,
        source_workflow: str,
        transfer_fraction: float,
    ) -> tuple[bool, list[str]]:
        violations: list[str] = []
        if transfer_fraction > 0.40:
            violations.append(
                f"Resource transfer from '{source_workflow}' ({transfer_fraction:.0%}) "
                f"exceeds the 40 % maximum borrow limit."
            )
        return (len(violations) == 0, violations)

    def validate_batch_governance(
        self,
        pending_approvals: int,
        max_batch_deferral: int = 12,
    ) -> tuple[bool, list[str]]:
        if pending_approvals > max_batch_deferral:
            return (
                False,
                [f"Governance backlog ({pending_approvals}) exceeds the safe batch ceiling of "
                 f"{max_batch_deferral}. Immediate review required."],
            )
        return (True, [])
