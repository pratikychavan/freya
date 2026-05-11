"""freya/org/__init__.py

Organizational Policy + Multi-Workflow Cognition layer.

Usage
-----
    from freya.org import OrganizationalCognitionPipeline

    pipeline = OrganizationalCognitionPipeline()
    result = pipeline.run(workflows=[...], resources=[...])
    print(pipeline.render(result))
"""
from __future__ import annotations

from freya.org.cognition import OrgCognitionResult, OrganizationalCognitionEngine
from freya.org.contention import ContentionAnalysis, OperationalContentionEngine
from freya.org.coordination import CoordinationPlan, WorkflowCoordinationEngine
from freya.org.models import (
    OrganizationalPolicy,
    OrganizationalWorkflowContext,
    SharedOperationalResource,
    WorkflowCoordinationDecision,
)
from freya.org.policy import OrganizationalPolicyEngine
from freya.org.prioritization import OrganizationalPrioritizationEngine, PrioritizationResult
from freya.org.rendering import (
    render_org_policy,
    render_org_summary,
    render_prioritization_decision,
    render_resource_pressure,
    render_workflow_coordination,
)
from freya.org.resources import SharedOperationalResourceEngine

__all__ = [
    # Pipeline
    "OrganizationalCognitionPipeline",
    # Engines
    "OrganizationalCognitionEngine",
    "OrganizationalPolicyEngine",
    "OrganizationalPrioritizationEngine",
    "OperationalContentionEngine",
    "WorkflowCoordinationEngine",
    "SharedOperationalResourceEngine",
    # Models
    "OrganizationalWorkflowContext",
    "SharedOperationalResource",
    "OrganizationalPolicy",
    "WorkflowCoordinationDecision",
    "OrgCognitionResult",
    "ContentionAnalysis",
    "CoordinationPlan",
    "PrioritizationResult",
    # Renderers
    "render_org_policy",
    "render_workflow_coordination",
    "render_resource_pressure",
    "render_prioritization_decision",
    "render_org_summary",
]


class OrganizationalCognitionPipeline:
    """Façade wiring all organizational cognition components.

    Parameters
    ----------
    llm_adapter:
        Optional async callable ``(request: dict) -> dict``.
        Currently reserved for future LLM-assisted prioritization.
    """

    def __init__(self, llm_adapter=None) -> None:
        self._cognition    = OrganizationalCognitionEngine(llm_adapter=llm_adapter)
        self._coordination = WorkflowCoordinationEngine()
        self._resources    = SharedOperationalResourceEngine()

    def run(
        self,
        workflows: list[OrganizationalWorkflowContext],
        resources: list[SharedOperationalResource] | None = None,
        pending_escalations: int = 0,
        pending_approvals: int = 0,
    ) -> dict:
        """Execute full organizational cognition + coordination.

        Returns dict with keys:
          cognition     OrgCognitionResult
          plan          CoordinationPlan
          resources     list[SharedOperationalResource]
        """
        res_list = resources or []

        cognition = self._cognition.reason(
            workflows=workflows,
            resources=res_list,
            pending_escalations=pending_escalations,
            pending_approvals=pending_approvals,
        )
        plan = self._coordination.plan(cognition)

        return {
            "cognition": cognition,
            "plan":      plan,
            "resources": res_list,
        }

    def render(self, result: dict, *, full: bool = True) -> str:
        """Produce a combined terminal display for a pipeline result."""
        cognition: OrgCognitionResult = result["cognition"]
        plan:      CoordinationPlan   = result["plan"]
        resources: list              = result["resources"]

        parts = [
            render_org_summary(cognition),
            render_workflow_coordination(plan),
        ]
        if full and resources:
            parts.append(render_resource_pressure(resources))
        if full and cognition.coordination_decisions:
            parts.append(render_prioritization_decision(cognition.coordination_decisions[:4]))
        return "\n".join(parts)

    def resource_engine(self) -> SharedOperationalResourceEngine:
        return self._resources
