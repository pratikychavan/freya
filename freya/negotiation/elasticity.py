"""freya/negotiation/elasticity.py

ElasticOperationalResourceEngine

Manages dynamic capacity borrowing between workflows.
All transfers are temporary, bounded, and reversible.
"""
from __future__ import annotations

import uuid

from freya.negotiation.models import ElasticResourceAdjustment

_MAX_BORROW_FRACTION = 0.40  # At most 40 % of a donor's capacity may be relocated.


class ElasticOperationalResourceEngine:
    """Produce and track elastic resource transfers between workflows."""

    def transfer(
        self,
        source_workflow: str,
        target_workflow: str,
        resource_id: str,
        source_capacity: float,
        requested_amount: float,
        duration_hint: str = "until_pressure_normalizes",
    ) -> ElasticResourceAdjustment:
        """Create a bounded, reversible resource transfer."""
        max_transferable = source_capacity * _MAX_BORROW_FRACTION
        amount = min(requested_amount, max_transferable)
        amount = max(amount, 0.0)

        return ElasticResourceAdjustment(
            resource_id=resource_id,
            source_workflow=source_workflow,
            target_workflow=target_workflow,
            adjustment_amount=round(amount, 4),
            temporary=True,
            duration_hint=duration_hint,
        )

    def rebalance(
        self,
        resource_id: str,
        workflow_capacities: dict[str, float],
        workflow_priorities: dict[str, str],
        needed_amount: float,
        target_workflow: str,
    ) -> list[ElasticResourceAdjustment]:
        """Distribute load from multiple donor workflows to a target.

        Donors are chosen in ascending priority order (background → low → standard).
        Each donor contributes proportionally until the needed amount is satisfied.
        """
        priority_order = ("background", "low", "standard", "high", "critical")
        donors = [
            wf for wf, prio in sorted(
                workflow_priorities.items(),
                key=lambda kv: priority_order.index(kv[1]) if kv[1] in priority_order else 99,
            )
            if wf != target_workflow and prio not in ("critical", "high")
        ]

        adjustments: list[ElasticResourceAdjustment] = []
        remaining = needed_amount

        for donor in donors:
            if remaining <= 0.0:
                break
            capacity = workflow_capacities.get(donor, 0.0)
            contribution = min(capacity * _MAX_BORROW_FRACTION, remaining)
            if contribution <= 0.0:
                continue
            adjustments.append(
                self.transfer(
                    source_workflow=donor,
                    target_workflow=target_workflow,
                    resource_id=resource_id,
                    source_capacity=capacity,
                    requested_amount=contribution,
                )
            )
            remaining -= contribution

        return adjustments

    def describe(self, adj: ElasticResourceAdjustment) -> list[str]:
        return [
            f"Resource:    {adj.resource_id}",
            f"From:        {adj.source_workflow}",
            f"To:          {adj.target_workflow}",
            f"Amount:      {adj.adjustment_amount:.1%} capacity units",
            f"Temporary:   {'Yes' if adj.temporary else 'No'}",
            f"Duration:    {adj.duration_hint}",
        ]
