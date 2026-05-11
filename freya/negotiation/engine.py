"""freya/negotiation/engine.py

DistributedOperationalNegotiationEngine

Central coordinator of the negotiation layer.
Accepts a snapshot of active workflows + resource state, selects the best
strategy, generates a NegotiationProposal, and produces concrete plans for
degradation and elastic reallocation.

Design rules adhered to here:
  - No autonomous swarm dynamics — all decisions are explainable.
  - Governance requirements are never traded away.
  - Critical workflows cannot degrade below safety floor.
  - All adjustments are reversible.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from freya.negotiation.contracts import OperationalNegotiationContractEngine
from freya.negotiation.degradation import GracefulOperationalDegradationEngine
from freya.negotiation.elasticity import ElasticOperationalResourceEngine
from freya.negotiation.governance import NegotiationGovernanceEngine
from freya.negotiation.models import (
    ElasticResourceAdjustment,
    NegotiationContract,
    NegotiationProposal,
    OperationalNegotiationRequest,
    WorkflowDegradationPlan,
)
from freya.negotiation.strategies import NegotiationStrategyEngine


@dataclass
class WorkflowSnapshot:
    """Lightweight representation of an active workflow for negotiation."""
    workflow_id:    str
    criticality:    str          # critical | high | standard | low | background
    priority:       str          # critical | high | standard | low | background
    resource_usage: float        # 0.0–1.0 fraction of allocated capacity
    current_quality: float = 1.0
    resource_id:    str = "reasoning_capacity"


@dataclass
class NegotiationResult:
    """Structured outcome of a single negotiation cycle."""
    proposal:       NegotiationProposal
    degradation_plans:   list[WorkflowDegradationPlan] = field(default_factory=list)
    resource_adjustments: list[ElasticResourceAdjustment] = field(default_factory=list)
    contracts:      list[NegotiationContract] = field(default_factory=list)
    governance_approved: bool = True
    governance_violations: list[str] = field(default_factory=list)


class DistributedOperationalNegotiationEngine:
    """Orchestrates multi-workflow operational negotiation under resource pressure."""

    def __init__(self) -> None:
        self._strategy   = NegotiationStrategyEngine()
        self._degradation = GracefulOperationalDegradationEngine()
        self._elasticity  = ElasticOperationalResourceEngine()
        self._contracts   = OperationalNegotiationContractEngine()
        self._governance  = NegotiationGovernanceEngine()

    def negotiate(
        self,
        workflows: list[WorkflowSnapshot],
        resource_pressure: float,
        pending_approvals: int = 0,
    ) -> NegotiationResult:
        """Run one negotiation cycle and return a validated NegotiationResult."""
        critical_workflows = {w.workflow_id for w in workflows if w.criticality == "critical"}
        has_critical = bool(critical_workflows)

        # 1. Select strategy
        strategy = self._strategy.select(
            resource_pressure=resource_pressure,
            pending_approvals=pending_approvals,
            has_critical_workflow=has_critical,
        )

        # 2. Identify requester (highest-priority workflow under most pressure)
        requester, donors = self._partition_workflows(workflows, critical_workflows)

        # 3. Build proposal skeleton from strategy engine
        donor_ids = [w.workflow_id for w in donors]
        req_obj = OperationalNegotiationRequest(
            workflow_id=requester.workflow_id if requester else "none",
            requested_resource=requester.resource_id if requester else "reasoning_capacity",
            requested_capacity=requester.resource_usage if requester else 0.0,
            operational_reason="resource_pressure",
            priority_level=requester.priority if requester else "standard",  # type: ignore[arg-type]
        )
        proposal = self._strategy.build_proposal(
            strategy=strategy,
            requester=req_obj,
            donor_workflows=donor_ids,
            resource_pressure=resource_pressure,
        )

        # 4. Produce concrete degradation plans (donors only)
        plans: list[WorkflowDegradationPlan] = []
        contracts: list[NegotiationContract] = []

        if strategy in ("temporary_degradation", "reasoning_compression", "optimization_deferral"):
            for donor in donors[:2]:  # Limit to 2 degraded workflows per cycle
                plan = self._degradation.plan(
                    workflow_id=donor.workflow_id,
                    criticality=donor.criticality,
                    current_pressure=resource_pressure,
                    current_quality=donor.current_quality,
                )
                if plan.degradation_mode != "none":
                    plans.append(plan)
                    contract = self._contracts.create(
                        workflow_id=donor.workflow_id,
                        contract_type="degradation",
                        extra_terms={"mode": plan.degradation_mode},
                    )
                    contracts.append(contract)

        # 5. Produce elastic resource transfers
        adjustments: list[ElasticResourceAdjustment] = []
        if strategy == "elastic_reallocation" and requester:
            capacities  = {w.workflow_id: 1.0 - w.resource_usage for w in workflows}
            priorities  = {w.workflow_id: w.priority for w in workflows}
            needed      = max(0.0, resource_pressure - 0.60)
            adjustments = self._elasticity.rebalance(
                resource_id=requester.resource_id,
                workflow_capacities=capacities,
                workflow_priorities=priorities,
                needed_amount=needed,
                target_workflow=requester.workflow_id,
            )
            for adj in adjustments:
                contract = self._contracts.create(
                    workflow_id=adj.source_workflow,
                    contract_type="resource_borrow",
                    extra_terms={"target": adj.target_workflow, "amount": str(adj.adjustment_amount)},
                )
                contracts.append(contract)

        # 6. Governance batching contracts
        if strategy == "governance_batching":
            if requester:
                contract = self._contracts.create(
                    workflow_id=requester.workflow_id,
                    contract_type="batching",
                    extra_terms={"pending_approvals": str(pending_approvals)},
                    expiry_trigger="backlog_cleared",
                )
                contracts.append(contract)

        # 7. Deferral contracts
        if strategy == "optimization_deferral":
            for donor in donors[:1]:
                contract = self._contracts.create(
                    workflow_id=donor.workflow_id,
                    contract_type="deferral",
                    extra_terms={"deferred_tasks": "background_optimization"},
                )
                contracts.append(contract)

        # 8. Governance validation
        approved, violations = self._governance.validate_proposal(proposal, plans, critical_workflows)

        return NegotiationResult(
            proposal=proposal,
            degradation_plans=plans,
            resource_adjustments=adjustments,
            contracts=contracts,
            governance_approved=approved,
            governance_violations=violations,
        )

    def recover(self, workflow_id: str) -> list[NegotiationContract]:
        """Revert and expire all active contracts for a recovering workflow."""
        return self._contracts.revert_all_for(workflow_id)

    def contract_summary(self) -> dict[str, int]:
        return self._contracts.summary()

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _partition_workflows(
        workflows: list[WorkflowSnapshot],
        critical_ids: set[str],
    ) -> tuple[WorkflowSnapshot | None, list[WorkflowSnapshot]]:
        priority_rank = {"critical": 5, "high": 4, "standard": 3, "low": 2, "background": 1}

        sorted_wf = sorted(
            workflows,
            key=lambda w: priority_rank.get(w.priority, 0),
            reverse=True,
        )
        if not sorted_wf:
            return None, []

        requester = sorted_wf[0]
        # Donors: everything that is not critical and not the requester
        donors = [
            w for w in sorted_wf[1:]
            if w.workflow_id not in critical_ids
        ]
        return requester, donors
