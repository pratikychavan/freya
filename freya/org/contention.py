"""freya/org/contention.py

OperationalContentionEngine

Detects competing workflows, resolves execution conflicts, and recommends
organizational rebalancing. Coordinates — does not dominate.
"""
from __future__ import annotations

from freya.org.models import (
    OrganizationalWorkflowContext,
    SharedOperationalResource,
    WorkflowCoordinationDecision,
)


class ContentionAnalysis:
    """Result of a contention assessment."""

    def __init__(
        self,
        contending_pairs: list[tuple[str, str, str]],   # (wf_a, wf_b, resource_id)
        decisions: list[WorkflowCoordinationDecision],
        escalation_load: str,
        governance_backlog: int,
        recommendations: list[str],
    ) -> None:
        self.contending_pairs   = contending_pairs
        self.decisions          = decisions
        self.escalation_load    = escalation_load
        self.governance_backlog = governance_backlog
        self.recommendations    = recommendations

    def is_stable(self) -> bool:
        return not self.contending_pairs and self.escalation_load in ("none", "low")


class OperationalContentionEngine:
    """Identifies and resolves cross-workflow execution conflicts."""

    def analyse(
        self,
        workflows: list[OrganizationalWorkflowContext],
        resources: list[SharedOperationalResource],
        pending_escalations: int = 0,
        pending_approvals: int = 0,
    ) -> ContentionAnalysis:
        # Find resource-level contention pairs
        contending_pairs: list[tuple[str, str, str]] = []
        decisions: list[WorkflowCoordinationDecision] = []

        for res in resources:
            if res.contention_level in ("high", "severe") and len(res.active_workflows) >= 2:
                wfs_in_res = [
                    w for w in workflows if w.workflow_id in res.active_workflows
                ]
                for i in range(len(wfs_in_res)):
                    for j in range(i + 1, len(wfs_in_res)):
                        a, b = wfs_in_res[i], wfs_in_res[j]
                        contending_pairs.append((a.workflow_id, b.workflow_id, res.resource_id))
                        decisions.append(
                            self._resolve(a, b, res)
                        )

        # Escalation load
        escalation_load = self._escalation_load(pending_escalations)
        gov_load        = self._gov_load(pending_approvals)

        recommendations = self._build_recommendations(
            contending_pairs, escalation_load, gov_load, pending_approvals
        )

        return ContentionAnalysis(
            contending_pairs=contending_pairs,
            decisions=decisions,
            escalation_load=escalation_load,
            governance_backlog=pending_approvals,
            recommendations=recommendations,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _resolve(
        a: OrganizationalWorkflowContext,
        b: OrganizationalWorkflowContext,
        res: SharedOperationalResource,
    ) -> WorkflowCoordinationDecision:
        """Simple: higher-criticality workflow wins."""
        _order = ["background", "low", "standard", "high", "critical"]
        a_score = _order.index(a.operational_criticality)
        b_score = _order.index(b.operational_criticality)

        if a_score >= b_score:
            winner, loser = a, b
        else:
            winner, loser = b, a

        return WorkflowCoordinationDecision(
            decision_type="rebalance",
            affected_workflows=[winner.workflow_id, loser.workflow_id],
            reason=(
                f"Resource '{res.resource_id}' contested "
                f"({res.contention_level} pressure={int(res.resource_pressure*100)}%). "
                f"'{winner.workflow_id}' ({winner.operational_criticality}) retains allocation; "
                f"'{loser.workflow_id}' ({loser.operational_criticality}) reduces consumption."
            ),
            operational_impact=(
                f"'{loser.workflow_id}' reduces {res.resource_type} usage. "
                "Contention pressure relieved."
            ),
            priority_boost_recipient=winner.workflow_id,
        )

    @staticmethod
    def _escalation_load(count: int) -> str:
        if count >= 5:
            return "severe"
        if count >= 3:
            return "high"
        if count >= 1:
            return "moderate"
        return "none"

    @staticmethod
    def _gov_load(pending: int) -> str:
        if pending >= 8:
            return "congested"
        if pending >= 4:
            return "elevated"
        return "normal"

    @staticmethod
    def _build_recommendations(
        pairs: list,
        escalation: str,
        gov_load: str,
        pending: int,
    ) -> list[str]:
        recs: list[str] = []
        if pairs:
            recs.append(
                f"{len(pairs)} resource contention pair(s) detected. "
                "Lower-priority workflows have been asked to reduce consumption."
            )
        if escalation in ("high", "severe"):
            recs.append(
                "Escalation queue is overloaded. Consider deferring non-critical approvals "
                "and simplifying low-priority workflows."
            )
        if gov_load in ("elevated", "congested"):
            recs.append(
                f"Governance approval backlog: {pending} pending. "
                "Reduce optimization interruptions in low-priority workflows."
            )
        if not recs:
            recs.append("No significant contention detected. Organizational state is stable.")
        return recs
