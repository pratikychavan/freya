"""freya/negotiation/__init__.py

Distributed Operational Negotiation Layer — public façade.

Quick start::

    from freya.negotiation import DistributedNegotiationPipeline
    from freya.negotiation.engine import WorkflowSnapshot

    pipeline = DistributedNegotiationPipeline()
    result = pipeline.run(
        workflows=[
            WorkflowSnapshot("wf-incident", "critical", "critical", 0.85),
            WorkflowSnapshot("wf-reporting", "low", "low",          0.40),
        ],
        resource_pressure=0.85,
        pending_approvals=2,
    )
    print(result["report"])
"""
from __future__ import annotations

from freya.negotiation.contracts import OperationalNegotiationContractEngine
from freya.negotiation.degradation import GracefulOperationalDegradationEngine
from freya.negotiation.elasticity import ElasticOperationalResourceEngine
from freya.negotiation.engine import (
    DistributedOperationalNegotiationEngine,
    NegotiationResult,
    WorkflowSnapshot,
)
from freya.negotiation.governance import NegotiationGovernanceEngine
from freya.negotiation.models import (
    ContractStatus,
    DegradationMode,
    ElasticResourceAdjustment,
    FlexibilityLevel,
    GovernanceRisk,
    NegotiationContract,
    NegotiationProposal,
    NegotiationStrategy,
    OperationalNegotiationRequest,
    PriorityLevel,
    WorkflowDegradationPlan,
)
from freya.negotiation.rendering import (
    render_degradation_plan,
    render_full_negotiation_state,
    render_negotiation_contract,
    render_negotiation_summary,
    render_resource_adjustment,
)
from freya.negotiation.strategies import NegotiationStrategyEngine


class DistributedNegotiationPipeline:
    """High-level façade wiring all negotiation components together.

    Typical usage: instantiate once, call ``run()`` whenever resource pressure
    or governance backlog crosses a threshold.
    """

    def __init__(self) -> None:
        self._engine = DistributedOperationalNegotiationEngine()

    def run(
        self,
        workflows: list[WorkflowSnapshot],
        resource_pressure: float,
        pending_approvals: int = 0,
    ) -> dict:
        """Execute one negotiation cycle.

        Returns a dict with keys:
          - ``result``: :class:`NegotiationResult`
          - ``report``: Human-readable string via :func:`render_full_negotiation_state`
          - ``approved``: bool — whether governance approved the proposal
          - ``violations``: list[str] — any governance violations
        """
        result: NegotiationResult = self._engine.negotiate(
            workflows=workflows,
            resource_pressure=resource_pressure,
            pending_approvals=pending_approvals,
        )
        report = render_full_negotiation_state(
            proposal=result.proposal,
            plans=result.degradation_plans,
            adjustments=result.resource_adjustments,
            contracts=result.contracts,
            approved=result.governance_approved,
            violations=result.governance_violations,
        )
        return {
            "result":     result,
            "report":     report,
            "approved":   result.governance_approved,
            "violations": result.governance_violations,
        }

    def recover(self, workflow_id: str) -> list[NegotiationContract]:
        """Revert all active contracts for a workflow that has recovered."""
        return self._engine.recover(workflow_id)

    def contract_summary(self) -> dict[str, int]:
        """Return count of contracts by status."""
        return self._engine.contract_summary()


__all__ = [
    # Pipeline façade
    "DistributedNegotiationPipeline",
    # Engine + snapshots
    "DistributedOperationalNegotiationEngine",
    "NegotiationResult",
    "WorkflowSnapshot",
    # Sub-engines (for direct use)
    "GracefulOperationalDegradationEngine",
    "ElasticOperationalResourceEngine",
    "OperationalNegotiationContractEngine",
    "NegotiationStrategyEngine",
    "NegotiationGovernanceEngine",
    # Models
    "OperationalNegotiationRequest",
    "NegotiationProposal",
    "WorkflowDegradationPlan",
    "ElasticResourceAdjustment",
    "NegotiationContract",
    # Literals
    "PriorityLevel",
    "FlexibilityLevel",
    "DegradationMode",
    "GovernanceRisk",
    "ContractStatus",
    "NegotiationStrategy",
    # Renderers
    "render_negotiation_summary",
    "render_degradation_plan",
    "render_resource_adjustment",
    "render_negotiation_contract",
    "render_full_negotiation_state",
]
