"""freya/steering/decisioning.py

OperationalSteeringEngine — applies user decisions to a WorkflowSteeringState
and derives downstream changes (strategy escalation, economics impact,
governance re-evaluation).

Steering directions:
  cost      → switch to deterministic strategy, drop premium preferences
  speed     → reduce analysis depth, skip non-essential sub-workflows
  quality   → escalate to cognitive strategy, re-enable deep comparisons
  balanced  → restore defaults

Each direction is applied as a deterministic state mutation — no LLM required.
"""
from __future__ import annotations

from typing import Any, Literal

from freya.steering.models import (
    NegotiationProposal,
    OperationalPreference,
    SteeringDecision,
    WorkflowSteeringState,
)

# Maps a user priority directive to concrete state mutations
_PRIORITY_MUTATIONS: dict[str, dict[str, Any]] = {
    "cost": {
        "strategy": "deterministic",
        "drop_preferences": ["premium"],
        "add_preferences": [
            OperationalPreference(
                preference_name="cost_sensitivity", preference_value="high", confidence=1.0
            )
        ],
    },
    "speed": {
        "strategy": "deterministic",
        "drop_preferences": [],
        "add_preferences": [
            OperationalPreference(
                preference_name="speed", preference_value="preferred", confidence=1.0
            )
        ],
    },
    "quality": {
        "strategy": "cognitive",
        "drop_preferences": ["cost_sensitivity"],
        "add_preferences": [
            OperationalPreference(
                preference_name="quality", preference_value="preferred", confidence=1.0
            )
        ],
    },
    "balanced": {
        "strategy": "hybrid",
        "drop_preferences": [],
        "add_preferences": [],
    },
}

# Human-readable narratives for each priority change
_PRIORITY_NARRATIVES: dict[str, str] = {
    "cost": "Prioritising lower cost. Switching to fast planning and dropping premium options.",
    "speed": "Prioritising speed. Reducing analysis depth for a faster result.",
    "quality": "Prioritising quality. Enabling deep comparison mode.",
    "balanced": "Balanced mode restored. All options considered equally.",
}


class OperationalSteeringEngine:
    """Apply user steering decisions to a WorkflowSteeringState."""

    def apply_choice(
        self,
        state: WorkflowSteeringState,
        proposal: NegotiationProposal,
        chosen_option_id: str,
    ) -> SteeringDecision:
        """Apply the chosen NegotiationOption to the state.

        Returns a SteeringDecision record capturing what changed.
        """
        option = next(
            (o for o in proposal.options if o.option_id == chosen_option_id), None
        )
        if option is None:
            raise ValueError(f"Option '{chosen_option_id}' not found in proposal '{proposal.proposal_id}'")

        updates: dict[str, Any] = {}

        for key, value in option.constraint_updates.items():
            if key == "strategy":
                state.set_strategy(value)
                updates["strategy"] = value
            elif key == "hotel_proximity":
                # Update preference rather than constraint
                self._set_preference(state, "hotel_proximity", str(value))
                updates["hotel_proximity"] = value
            elif key == "hotel_tier":
                self._set_preference(state, "hotel_tier", value)
                updates["hotel_tier"] = value
            elif key == "flight_class":
                self._set_preference(state, "flight_class", value)
                updates["flight_class"] = value
            else:
                state.update_constraint(key, value)
                updates[key] = value

        decision = SteeringDecision(
            proposal_id=proposal.proposal_id,
            chosen_option_id=chosen_option_id,
            applied_updates=updates,
            narrative=f"Applied: {option.title}. {option.impact_summary}",
        )
        state.decisions_made.append(decision)
        return decision

    def steer_priority(
        self,
        state: WorkflowSteeringState,
        priority: Literal["cost", "speed", "quality", "balanced"],
    ) -> SteeringDecision:
        """Steer the workflow to a new priority directive.

        This is a coarser-grained action than picking a negotiation option.
        It applies the full mutation bundle for the given priority.
        """
        mutations = _PRIORITY_MUTATIONS.get(priority, {})
        applied: dict[str, Any] = {}

        strategy = mutations.get("strategy")
        if strategy:
            state.set_strategy(strategy)
            applied["strategy"] = strategy

        state.set_priority(priority)
        applied["priority"] = priority

        drop = mutations.get("drop_preferences", [])
        state.preferences = [
            p for p in state.preferences if p.preference_name not in drop
        ]

        for pref in mutations.get("add_preferences", []):
            self._set_preference(state, pref.preference_name, pref.preference_value, pref.confidence)
            applied[pref.preference_name] = pref.preference_value

        narrative = _PRIORITY_NARRATIVES.get(priority, f"Priority set to {priority}.")
        decision = SteeringDecision(
            proposal_id="priority_steer",
            chosen_option_id=priority,
            applied_updates=applied,
            narrative=narrative,
        )
        state.decisions_made.append(decision)
        return decision

    def modify_constraint(
        self,
        state: WorkflowSteeringState,
        name: str,
        value: Any,
    ) -> SteeringDecision:
        """Directly update a single constraint value.

        Used when the user explicitly says e.g. 'increase budget to ₹50k'.
        """
        old_value = state.constraints.get(name)
        state.update_constraint(name, value)

        label = name.replace("_", " ").title()
        old_str = f" (was {old_value.value})" if old_value else ""
        decision = SteeringDecision(
            proposal_id="direct_modify",
            chosen_option_id=f"set_{name}",
            applied_updates={name: value},
            narrative=f"{label} updated to {value}{old_str}.",
        )
        state.decisions_made.append(decision)
        return decision

    # ── helpers ────────────────────────────────────────────────────────

    def _set_preference(
        self,
        state: WorkflowSteeringState,
        name: str,
        value: str,
        confidence: float = 1.0,
    ) -> None:
        existing = next((p for p in state.preferences if p.preference_name == name), None)
        if existing:
            state.preferences.remove(existing)
        state.preferences.append(
            OperationalPreference(
                preference_name=name, preference_value=value, confidence=confidence
            )
        )

    def governance_impact(self, state: WorkflowSteeringState) -> list[str]:
        """Return governance requirements implied by the current steering state.

        Integrates with the governance layer — callers can pass these to
        GovernanceEngine.evaluate_requirements().
        """
        reqs: list[str] = []
        budget_c = state.get_constraint("budget_inr")
        if budget_c and float(budget_c.value) > 75_000:
            reqs.append("high_value_approval_required")
        elif budget_c and float(budget_c.value) > 30_000:
            reqs.append("manager_approval_required")
        if state.strategy == "cognitive":
            reqs.append("cost_tracking_required")
        if state.priority == "quality":
            reqs.append("quality_sign_off_required")
        return reqs

    def economics_impact(self, state: WorkflowSteeringState) -> dict[str, Any]:
        """Summarise how the current steering state affects execution economics."""
        budget_c = state.get_constraint("budget_inr")
        budget = float(budget_c.value) if budget_c else 0.0
        strategy_cost_multiplier = {
            "deterministic": 0.6,
            "hybrid": 1.0,
            "cognitive": 1.4,
        }.get(state.strategy, 1.0)

        return {
            "total_budget": budget,
            "strategy": state.strategy,
            "estimated_llm_cost_multiplier": strategy_cost_multiplier,
            "priority": state.priority,
            "within_budget_estimate": budget > 0,
        }
