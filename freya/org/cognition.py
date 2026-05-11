"""freya/org/cognition.py

OrganizationalCognitionEngine

Reasons across the full set of active workflows to produce a holistic
organizational operational assessment. Deterministic-first; LLM optional.
"""
from __future__ import annotations

from typing import Callable, Awaitable

from freya.org.contention import ContentionAnalysis, OperationalContentionEngine
from freya.org.models import (
    OrganizationalPolicy,
    OrganizationalWorkflowContext,
    SharedOperationalResource,
    WorkflowCoordinationDecision,
)
from freya.org.policy import OrganizationalPolicyEngine
from freya.org.prioritization import OrganizationalPrioritizationEngine, PrioritizationResult

LLMAdapter = Callable[[dict], Awaitable[dict]]


class OrgCognitionResult:
    """Full organizational reasoning output."""

    def __init__(
        self,
        prioritization: PrioritizationResult,
        contention: ContentionAnalysis,
        policies: dict[str, OrganizationalPolicy],
        org_summary: list[str],
        coordination_decisions: list[WorkflowCoordinationDecision],
        budget_pressure: str,
    ) -> None:
        self.prioritization          = prioritization
        self.contention              = contention
        self.policies                = policies
        self.org_summary             = org_summary
        self.coordination_decisions  = coordination_decisions
        self.budget_pressure         = budget_pressure

    def is_stable(self) -> bool:
        return self.contention.is_stable() and self.budget_pressure in ("none", "low")


class OrganizationalCognitionEngine:
    """Cross-workflow reasoning engine."""

    def __init__(self, llm_adapter: LLMAdapter | None = None) -> None:
        self._policy    = OrganizationalPolicyEngine()
        self._priority  = OrganizationalPrioritizationEngine()
        self._contention= OperationalContentionEngine()
        self._llm       = llm_adapter

    def reason(
        self,
        workflows: list[OrganizationalWorkflowContext],
        resources: list[SharedOperationalResource],
        pending_escalations: int = 0,
        pending_approvals: int = 0,
    ) -> OrgCognitionResult:
        # 1. Policy resolution per workflow
        policies = {
            wf.workflow_id: self._policy.resolve(wf.workflow_domain)
            for wf in workflows
        }

        # 2. Prioritization
        prioritization = self._priority.rank(workflows)

        # 3. Contention analysis
        contention = self._contention.analyse(
            workflows, resources, pending_escalations, pending_approvals
        )

        # 4. Budget pressure
        budget_pressure = self._budget_pressure(resources)

        # 5. Org summary
        org_summary = self._build_summary(
            workflows, prioritization, contention, budget_pressure,
            pending_approvals, pending_escalations,
        )

        # 6. Merge coordination decisions
        all_decisions = prioritization.decisions + contention.decisions

        return OrgCognitionResult(
            prioritization=prioritization,
            contention=contention,
            policies=policies,
            org_summary=org_summary,
            coordination_decisions=all_decisions,
            budget_pressure=budget_pressure,
        )

    # ── Private ────────────────────────────────────────────────────────────────

    @staticmethod
    def _budget_pressure(resources: list[SharedOperationalResource]) -> str:
        if not resources:
            return "none"
        max_pressure = max((r.resource_pressure for r in resources), default=0.0)
        if max_pressure >= 0.88:
            return "critical"
        if max_pressure >= 0.75:
            return "high"
        if max_pressure >= 0.55:
            return "moderate"
        if max_pressure >= 0.30:
            return "low"
        return "none"

    @staticmethod
    def _build_summary(
        workflows: list[OrganizationalWorkflowContext],
        prio: PrioritizationResult,
        contention: ContentionAnalysis,
        budget_pressure: str,
        pending_approvals: int,
        pending_escalations: int,
    ) -> list[str]:
        lines: list[str] = []
        lines.append(f"Active workflows: {len(workflows)}")
        if prio.top():
            top = prio.top()
            lines.append(
                f"Highest priority: '{top.workflow_id}' "  # type: ignore[union-attr]
                f"({top.workflow_domain}, criticality={top.operational_criticality})"  # type: ignore[union-attr]
            )
        if contention.contending_pairs:
            lines.append(
                f"Resource contention: {len(contention.contending_pairs)} pair(s)"
            )
        if budget_pressure not in ("none", "low"):
            lines.append(f"Shared budget pressure: {budget_pressure}")
        if pending_approvals > 0:
            lines.append(f"Pending governance approvals: {pending_approvals}")
        if pending_escalations > 0:
            lines.append(f"Pending escalations: {pending_escalations}")
        if not lines[1:]:
            lines.append("Organizational state is stable.")
        return lines
