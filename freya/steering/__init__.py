"""freya/steering/__init__.py

Public API for the Constraint Negotiation + Operational Steering layer.

Quick start::

    from freya.steering import SteeringCoordinator
    from freya.steering.models import OperationalConstraint, OperationalPreference

    state = SteeringCoordinator.build_state(
        goal="Plan Bangalore trip",
        budget_inr=40_000,
        nights=2,
        preferences=["hotel_proximity"],
    )
    coordinator = SteeringCoordinator()
    proposals = coordinator.negotiate(state)
    recs = coordinator.recommend(state)
"""
from freya.steering.decisioning import OperationalSteeringEngine
from freya.steering.models import (
    NegotiationOption,
    NegotiationProposal,
    OperationalConstraint,
    OperationalPreference,
    SteeringDecision,
    WorkflowSteeringState,
)
from freya.steering.negotiation import ConstraintNegotiationEngine
from freya.steering.preferences import PreferenceMemory
from freya.steering.recommendations import (
    OperationalRecommendation,
    OperationalRecommendationEngine,
)
from freya.steering.rendering import (
    render_negotiation,
    render_operational_update,
    render_recommendation,
    render_recommendations,
    render_steering_state,
)


class SteeringCoordinator:
    """Façade that wires negotiation, decisioning, preferences and recommendations.

    Typical usage::

        coordinator = SteeringCoordinator()
        state = SteeringCoordinator.build_state("My trip", budget_inr=40_000, nights=2)
        proposals = coordinator.negotiate(state)
        # show proposals to user, collect choice…
        decision = coordinator.apply_choice(state, proposals[0], "economy_flight")
        recs = coordinator.recommend(state)
    """

    def __init__(self, memory: PreferenceMemory | None = None) -> None:
        self._negotiator = ConstraintNegotiationEngine()
        self._steerer = OperationalSteeringEngine()
        self._recommender = OperationalRecommendationEngine()
        self._memory = memory or PreferenceMemory(persist_path=None)

    # ── State builder ────────────────────────────────────────────────

    @staticmethod
    def build_state(
        goal: str,
        *,
        budget_inr: int | float | None = None,
        nights: int | None = None,
        preferences: list[str] | None = None,
        strategy: str = "hybrid",
        priority: str = "balanced",
    ) -> WorkflowSteeringState:
        """Convenience factory for WorkflowSteeringState."""
        constraints: dict[str, OperationalConstraint] = {}
        if budget_inr is not None:
            constraints["budget_inr"] = OperationalConstraint(
                name="budget_inr", value=int(budget_inr), negotiable=True
            )
        if nights is not None:
            constraints["nights"] = OperationalConstraint(
                name="nights", value=nights, negotiable=True
            )

        prefs: list[OperationalPreference] = []
        for pref_name in (preferences or []):
            prefs.append(
                OperationalPreference(
                    preference_name=pref_name,
                    preference_value="preferred",
                    confidence=1.0,
                )
            )

        state = WorkflowSteeringState(
            goal=goal,
            constraints=constraints,
            preferences=prefs,
            strategy=strategy,  # type: ignore[arg-type]
            priority=priority,  # type: ignore[arg-type]
        )
        return state

    # ── Negotiation ──────────────────────────────────────────────────

    def negotiate(self, state: WorkflowSteeringState) -> list[NegotiationProposal]:
        """Detect conflicts and return negotiation proposals."""
        return self._negotiator.detect(state)

    def apply_choice(
        self,
        state: WorkflowSteeringState,
        proposal: NegotiationProposal,
        chosen_option_id: str,
    ) -> SteeringDecision:
        """Apply a chosen option and record the preference."""
        decision = self._steerer.apply_choice(state, proposal, chosen_option_id)
        self._memory.record_decision(decision)
        return decision

    # ── Priority steering ────────────────────────────────────────────

    def steer(self, state: WorkflowSteeringState, priority: str) -> SteeringDecision:
        """Steer the workflow to a new priority (cost/speed/quality/balanced)."""
        decision = self._steerer.steer_priority(state, priority)  # type: ignore[arg-type]
        self._memory.record_decision(decision)
        return decision

    def modify_constraint(
        self, state: WorkflowSteeringState, name: str, value: object
    ) -> SteeringDecision:
        """Directly update a constraint value."""
        decision = self._steerer.modify_constraint(state, name, value)
        self._memory.record_decision(decision)
        return decision

    # ── Recommendations ──────────────────────────────────────────────

    def recommend(self, state: WorkflowSteeringState) -> list[OperationalRecommendation]:
        """Return proactive operational recommendations."""
        return self._recommender.recommend(state)

    # ── Integration helpers ──────────────────────────────────────────

    def governance_impact(self, state: WorkflowSteeringState) -> list[str]:
        """Return governance requirements implied by current steering state."""
        return self._steerer.governance_impact(state)

    def economics_impact(self, state: WorkflowSteeringState) -> dict:
        """Return economics summary for the current steering state."""
        return self._steerer.economics_impact(state)

    # ── Memory ───────────────────────────────────────────────────────

    @property
    def memory(self) -> PreferenceMemory:
        return self._memory


__all__ = [
    "SteeringCoordinator",
    # Models
    "OperationalConstraint",
    "NegotiationOption",
    "NegotiationProposal",
    "OperationalPreference",
    "SteeringDecision",
    "WorkflowSteeringState",
    # Engines
    "ConstraintNegotiationEngine",
    "OperationalSteeringEngine",
    "OperationalRecommendationEngine",
    "PreferenceMemory",
    # Recommendations
    "OperationalRecommendation",
    # Rendering
    "render_negotiation",
    "render_recommendation",
    "render_recommendations",
    "render_operational_update",
    "render_steering_state",
]
