"""Governance policies for the Business Travel demo.

HotelOverBudgetPolicy: Requires HITL approval when the selected hotel
exceeds the preferred nightly budget. Only fires once (before build_itinerary
is completed).

TravelStrategyEngine: Extends ExecutionStrategyEngine to detect when
the planner has set context.planning_mode = COGNITIVE, allowing the
strategy timeline to correctly reflect cognitive escalation.
"""
from __future__ import annotations

from freya.governance.base import InterventionPolicy
from freya.governance.models import GovernanceDecision, InterventionDecision
from freya.planner.mode import PlanningMode
from freya.strategies.engine import ExecutionStrategyEngine
from freya.strategies.models import ExecutionStrategy, StrategyDecision
from freya.strategies.signals import RuntimeSignals


class HotelOverBudgetPolicy(InterventionPolicy):
    """Require approval when the selected hotel exceeds the preferred budget.

    Fires on iterations where compare_hotels is done but build_itinerary
    has NOT yet been completed (i.e., the checkpoint has not been passed).
    """

    def __init__(
        self,
        budget_per_night_inr: int = 12_000,
        nights: int = 2,
    ) -> None:
        self.budget_per_night = budget_per_night_inr
        self.nights = nights

    def evaluate(
        self,
        planning_context: object,
        proposed_dag: object,
    ) -> GovernanceDecision:
        completed = list(getattr(planning_context, "completed_tasks", []))

        # Only fire if compare_hotels is done AND build_itinerary not yet completed
        # (prevents re-firing the approval after we have already been approved)
        if "compare_hotels" not in completed:
            return GovernanceDecision(
                decision=InterventionDecision.APPROVE,
                reason="Hotel selection not yet made.",
            )
        if "build_itinerary" in completed:
            return GovernanceDecision(
                decision=InterventionDecision.APPROVE,
                reason="Hotel already approved — itinerary in progress.",
            )

        task_results = getattr(planning_context, "task_results", {})
        hotel_result = task_results.get("compare_hotels", {})
        output = (hotel_result.get("output") or {})
        selected = output.get("selected_hotel", {})

        if not selected:
            return GovernanceDecision(
                decision=InterventionDecision.APPROVE,
                reason="No hotel selection found in context.",
            )

        price = selected.get("price_per_night_inr", 0)
        if price > self.budget_per_night:
            total = price * self.nights
            limit = self.budget_per_night * self.nights
            return GovernanceDecision(
                decision=InterventionDecision.REQUIRE_APPROVAL,
                reason=(
                    f"Selected hotel '{selected.get('name', '?')}' costs "
                    f"₹{price:,}/night (₹{total:,} for {self.nights} nights), "
                    f"exceeding preferred budget of ₹{limit:,} "
                    f"(₹{self.budget_per_night:,}/night)."
                ),
                risk_level="medium",
                triggered_policies=["HotelOverBudgetPolicy"],
            )

        return GovernanceDecision(
            decision=InterventionDecision.APPROVE,
            reason=f"Hotel ₹{price:,}/night is within preferred budget of ₹{self.budget_per_night:,}.",
        )


class TravelStrategyEngine(ExecutionStrategyEngine):
    """Strategy engine that also detects cognitive escalation from the planner.

    When the TravelPlanner sets context.planning_mode = COGNITIVE, this engine
    returns a COGNITIVE strategy decision so the timeline correctly reflects
    the escalation.
    """

    def select_strategy(
        self,
        planning_context: object,
        workflow_state: object,
        runtime_signals: RuntimeSignals,
    ) -> StrategyDecision:
        mode = getattr(planning_context, "planning_mode", None)
        if mode == PlanningMode.COGNITIVE:
            return StrategyDecision(
                strategy=ExecutionStrategy.COGNITIVE,
                reason="TravelPlanner requested cognitive strategy for hotel comparison.",
                confidence=0.95,
                triggered_by=["planner_requested_cognitive_mode"],
            )
        return super().select_strategy(planning_context, workflow_state, runtime_signals)
