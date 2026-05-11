"""freya/org/coordination.py

WorkflowCoordinationEngine

Coordinates workflow interactions: defers low-priority work, rebalances
reasoning depth, redistributes budget, and synchronizes governance timing.
Coordinates — not dominates.
"""
from __future__ import annotations

from freya.org.models import (
    OrganizationalWorkflowContext,
    SharedOperationalResource,
    WorkflowCoordinationDecision,
)
from freya.org.cognition import OrgCognitionResult
from freya.org.resources import SharedOperationalResourceEngine


class CoordinationPlan:
    """Executable coordination instructions for a set of workflows."""

    def __init__(
        self,
        decisions: list[WorkflowCoordinationDecision],
        deferred: list[str],
        prioritized: list[str],
        rebalanced: list[str],
        rationale: list[str],
    ) -> None:
        self.decisions   = decisions
        self.deferred    = deferred       # workflow_ids to defer
        self.prioritized = prioritized    # workflow_ids with boosted resources
        self.rebalanced  = rebalanced     # workflow_ids whose budgets changed
        self.rationale   = rationale


class WorkflowCoordinationEngine:
    """Translates OrgCognitionResult into actionable coordination plans."""

    def __init__(self, resource_engine: SharedOperationalResourceEngine | None = None) -> None:
        self._resources = resource_engine or SharedOperationalResourceEngine()

    def plan(self, cognition: OrgCognitionResult) -> CoordinationPlan:
        """Produce a CoordinationPlan from organizational cognition output."""
        decisions:   list[WorkflowCoordinationDecision] = list(cognition.coordination_decisions)
        deferred:    list[str] = []
        prioritized: list[str] = []
        rebalanced:  list[str] = []
        rationale:   list[str] = list(cognition.prioritization.rationale)

        # Collect deferred/prioritized from decisions
        for d in decisions:
            if d.decision_type == "defer":
                deferred.extend(d.affected_workflows)
            elif d.decision_type == "prioritize":
                if d.priority_boost_recipient:
                    prioritized.append(d.priority_boost_recipient)
            elif d.decision_type == "rebalance":
                rebalanced.extend(d.affected_workflows)

        # Governance load → reduce reasoning for lower-priority deferred workflows
        if cognition.contention.governance_backlog >= 4:
            for wf_id in deferred:
                decisions.append(WorkflowCoordinationDecision(
                    decision_type="reduce_reasoning",
                    affected_workflows=[wf_id],
                    reason=(
                        f"Governance approval backlog ({cognition.contention.governance_backlog}) "
                        "too high — reducing reasoning depth for deferred workflows."
                    ),
                    operational_impact=(
                        "Lower reasoning depth reduces governance review interruptions "
                        "and approval bandwidth consumption."
                    ),
                ))
                rationale.append(
                    f"Reduced reasoning depth for '{wf_id}' due to governance backlog."
                )

        # Budget pressure → governance gate non-critical workflows
        if cognition.budget_pressure in ("high", "critical"):
            prio_ids = {wf.workflow_id for wf in cognition.prioritization.ordered[:1]}
            for wf in cognition.prioritization.ordered[1:]:
                if wf.operational_criticality in ("low", "background"):
                    decisions.append(WorkflowCoordinationDecision(
                        decision_type="governance_gate",
                        affected_workflows=[wf.workflow_id],
                        reason=(
                            f"Shared budget pressure is {cognition.budget_pressure}. "
                            f"'{wf.workflow_id}' requires governance approval before "
                            "consuming additional resources."
                        ),
                        operational_impact=(
                            "Workflow paused pending governance review of budget allocation."
                        ),
                    ))
                    rationale.append(
                        f"Budget gate applied to '{wf.workflow_id}' "
                        f"(pressure={cognition.budget_pressure})."
                    )

        # Add contention recommendations to rationale
        rationale.extend(cognition.contention.recommendations)

        return CoordinationPlan(
            decisions=decisions,
            deferred=list(set(deferred)),
            prioritized=list(set(prioritized)),
            rebalanced=list(set(rebalanced)),
            rationale=rationale,
        )

    def describe_plan(self, plan: CoordinationPlan) -> list[str]:
        """Produce human-readable coordination plan lines."""
        lines: list[str] = []
        if plan.prioritized:
            lines.append(f"Prioritized: {', '.join(plan.prioritized)}")
        if plan.deferred:
            lines.append(f"Deferred: {', '.join(plan.deferred)}")
        if plan.rebalanced:
            lines.append(f"Rebalanced: {', '.join(plan.rebalanced)}")
        for d in plan.decisions:
            lines.append(f"[{d.decision_type}] {d.reason[:100]}")
        return lines
