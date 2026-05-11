"""freya/steering/models.py

Core data models for the Constraint Negotiation + Operational Steering layer.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OperationalConstraint(BaseModel):
    """A named constraint on the workflow, with negotiability metadata."""

    name: str                                  # e.g. "budget_inr", "nights"
    value: str | int | float | bool            # current value
    priority: Literal["must", "prefer", "nice_to_have"] = "prefer"
    negotiable: bool = True                    # can Freya propose alternatives?


class NegotiationOption(BaseModel):
    """One concrete alternative offered during constraint negotiation."""

    option_id: str                             # short slug, e.g. "increase_budget"
    title: str                                 # user-facing headline
    description: str                           # what it means
    impact_summary: str                        # human-readable tradeoff
    estimated_cost_change: float | None = None # +ve = more expensive, -ve = savings
    estimated_time_change: float | None = None # in hours, +ve = longer
    constraint_updates: dict[str, Any] = Field(default_factory=dict)
    # ^ applied to OperationalConstraint.value when user picks this option


class NegotiationProposal(BaseModel):
    """A detected conflict with one or more resolution options."""

    proposal_id: str
    reason: str                  # why a negotiation is needed
    detected_conflict: str       # short slug, e.g. "hotel_over_budget"
    options: list[NegotiationOption]
    recommended_option_id: str | None = None   # which option Freya recommends


class OperationalPreference(BaseModel):
    """An inferred or stated user preference."""

    preference_name: str         # e.g. "cost_sensitivity", "convenience", "speed"
    preference_value: str        # e.g. "high", "low", "preferred"
    confidence: float = 0.8      # 0-1, how sure we are


class SteeringDecision(BaseModel):
    """The result of a user choosing a NegotiationOption."""

    proposal_id: str
    chosen_option_id: str
    applied_updates: dict[str, Any]            # constraint values actually changed
    narrative: str                             # one-line summary shown to user


class WorkflowSteeringState(BaseModel):
    """Live operational state of a running/planned workflow."""

    goal: str
    constraints: dict[str, OperationalConstraint] = Field(default_factory=dict)
    preferences: list[OperationalPreference] = Field(default_factory=list)
    active_proposals: list[NegotiationProposal] = Field(default_factory=list)
    decisions_made: list[SteeringDecision] = Field(default_factory=list)
    strategy: Literal["deterministic", "cognitive", "hybrid"] = "hybrid"
    priority: Literal["cost", "speed", "quality", "balanced"] = "balanced"

    def get_constraint(self, name: str) -> OperationalConstraint | None:
        return self.constraints.get(name)

    def update_constraint(self, name: str, value: Any) -> None:
        if name in self.constraints:
            self.constraints[name] = self.constraints[name].model_copy(update={"value": value})
        else:
            self.constraints[name] = OperationalConstraint(name=name, value=value)

    def set_priority(self, priority: str) -> None:
        allowed = {"cost", "speed", "quality", "balanced"}
        if priority in allowed:
            self.priority = priority  # type: ignore[assignment]

    def set_strategy(self, strategy: str) -> None:
        allowed = {"deterministic", "cognitive", "hybrid"}
        if strategy in allowed:
            self.strategy = strategy  # type: ignore[assignment]
