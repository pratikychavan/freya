"""freya/org/prioritization.py

OrganizationalPrioritizationEngine

Resolves competing workflow priorities organizationally.
Decisions are explainable, policy-driven, and fair — not opaque.
"""
from __future__ import annotations

from freya.org.models import (
    OperationalCriticality,
    OrganizationalWorkflowContext,
    WorkflowCoordinationDecision,
)

# Criticality → numeric score (higher = more priority)
_CRITICALITY_SCORE: dict[OperationalCriticality, int] = {
    "critical":   5,
    "high":       4,
    "standard":   3,
    "low":        2,
    "background": 1,
}

# Domain priority boosts
_DOMAIN_BOOSTS: dict[str, int] = {
    "incident": 3,
    "incident_response": 3,
    "emergency": 3,
    "security": 2,
    "executive": 2,
    "finance": 1,
}


class PrioritizationResult:
    """Ordered list of workflows with reasoning."""

    def __init__(
        self,
        ordered: list[OrganizationalWorkflowContext],
        decisions: list[WorkflowCoordinationDecision],
        rationale: list[str],
    ) -> None:
        self.ordered   = ordered    # highest priority first
        self.decisions = decisions
        self.rationale = rationale

    def top(self) -> OrganizationalWorkflowContext | None:
        return self.ordered[0] if self.ordered else None


class OrganizationalPrioritizationEngine:
    """Ranks and coordinates workflows by organizational priority."""

    def rank(
        self,
        workflows: list[OrganizationalWorkflowContext],
    ) -> PrioritizationResult:
        """Sort workflows by organizational priority; generate decisions."""
        if not workflows:
            return PrioritizationResult([], [], [])

        scored = [
            (self._score(wf), wf)
            for wf in workflows
        ]
        scored.sort(key=lambda x: -x[0])
        ordered = [wf for _, wf in scored]

        decisions: list[WorkflowCoordinationDecision] = []
        rationale: list[str] = []

        # Top workflow gets a priority notice
        top = ordered[0]
        rationale.append(
            f"Workflow '{top.workflow_id}' ({top.workflow_domain}) ranked highest "
            f"(criticality={top.operational_criticality}, "
            f"priority={top.organizational_priority})."
        )

        # Lower-priority workflows get deferral decisions
        for wf in ordered[1:]:
            if self._score(wf) < self._score(top) - 1:
                decisions.append(WorkflowCoordinationDecision(
                    decision_type="defer",
                    affected_workflows=[wf.workflow_id],
                    reason=(
                        f"'{top.workflow_id}' is higher-priority "
                        f"({top.operational_criticality}). "
                        f"'{wf.workflow_id}' is deferred to preserve execution resources."
                    ),
                    operational_impact=(
                        "Lower-priority workflow execution delayed; "
                        "resources redirected to critical workflow."
                    ),
                    priority_boost_recipient=top.workflow_id,
                ))
                rationale.append(
                    f"Workflow '{wf.workflow_id}' deferred (score gap too large)."
                )

        # If top is incident-response, emit explicit prioritization decision
        if top.workflow_domain.lower() in ("incident", "incident_response", "emergency"):
            decisions.insert(0, WorkflowCoordinationDecision(
                decision_type="prioritize",
                affected_workflows=[top.workflow_id],
                reason="Incident-response workflow detected — temporarily prioritized.",
                operational_impact=(
                    "Incident-response workflow receives full execution priority. "
                    "All non-critical workflows temporarily deferred."
                ),
                priority_boost_recipient=top.workflow_id,
            ))

        return PrioritizationResult(ordered=ordered, decisions=decisions, rationale=rationale)

    def resolve_contention(
        self,
        high: OrganizationalWorkflowContext,
        low: OrganizationalWorkflowContext,
        resource: str,
    ) -> WorkflowCoordinationDecision:
        """Produce a contention-resolution decision for two competing workflows."""
        return WorkflowCoordinationDecision(
            decision_type="rebalance",
            affected_workflows=[high.workflow_id, low.workflow_id],
            reason=(
                f"Resource '{resource}' contested. '{high.workflow_id}' "
                f"({high.operational_criticality}) takes priority over "
                f"'{low.workflow_id}' ({low.operational_criticality})."
            ),
            operational_impact=(
                f"'{low.workflow_id}' reduces {resource} consumption; "
                f"'{high.workflow_id}' maintains full allocation."
            ),
            priority_boost_recipient=high.workflow_id,
        )

    # ── Private ────────────────────────────────────────────────────────────────

    @staticmethod
    def _score(wf: OrganizationalWorkflowContext) -> float:
        base      = _CRITICALITY_SCORE.get(wf.operational_criticality, 3)
        domain_bst= _DOMAIN_BOOSTS.get(wf.workflow_domain.lower(), 0)
        weight     = wf.execution_budget_weight
        return (base + domain_bst) * weight
