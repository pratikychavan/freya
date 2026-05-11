"""freya/optimization/__init__.py

Public API for the Proactive Operational Optimization layer.

Quick start::

    from freya.optimization import OptimizationAdvisor
    from freya.steering import SteeringCoordinator

    state = SteeringCoordinator.build_state("Plan Bangalore trip", budget_inr=40_000, nights=2)
    advisor = OptimizationAdvisor()
    proposal = advisor.propose(state)
    if proposal:
        print(render_optimization_proposal(proposal))
"""
from freya.optimization.engine import ProactiveOptimizationEngine
from freya.optimization.models import (
    OptimizationEvaluation,
    OptimizationOpportunity,
    OptimizationProposal,
)
from freya.optimization.policies import OptimizationGovernancePolicy, PolicyDecision
from freya.optimization.recommendations import OperationalOptimizationRecommender
from freya.optimization.rendering import (
    render_optimization_evaluation,
    render_optimization_proposal,
    render_optimization_summary,
)
from freya.optimization.scoring import OptimizationScoringEngine
from freya.steering.models import WorkflowSteeringState


class OptimizationAdvisor:
    """Top-level façade for the proactive optimization layer.

    Combines engine, scoring, policy and recommendations into a single entry point.

    IMPORTANT: This advisor NEVER auto-applies changes. All proposals require
    explicit acceptance by the caller before any state mutation occurs.
    """

    def __init__(self) -> None:
        self._recommender = OperationalOptimizationRecommender()
        self._engine = ProactiveOptimizationEngine()
        self._scorer = OptimizationScoringEngine()
        self._policy = OptimizationGovernancePolicy()

    def propose(self, state: WorkflowSteeringState) -> OptimizationProposal | None:
        """Analyse the state and return an OptimizationProposal if opportunities exist."""
        return self._recommender.propose(state)

    def evaluate(self, state: WorkflowSteeringState) -> OptimizationEvaluation:
        """Score the current state without generating a full proposal."""
        return self._recommender.evaluate_only(state)

    def top_opportunity(self, state: WorkflowSteeringState) -> OptimizationOpportunity | None:
        """Return only the single highest-value opportunity."""
        return self._recommender.top_opportunity(state)

    def apply_opportunity(
        self,
        state: WorkflowSteeringState,
        opportunity: OptimizationOpportunity,
    ) -> dict:
        """Apply an opportunity's constraint_updates to the state.

        Returns the dict of changes made.
        Raises ValueError if the policy blocks or requires approval that was not granted.
        """
        decision = self._policy.evaluate(opportunity)
        if decision.verdict == "block":
            raise ValueError(f"Optimization blocked by policy: {decision.reason}")
        if decision.verdict == "require_approval":
            raise ValueError(
                f"This optimization requires approval before it can be applied: {decision.reason}"
            )

        applied = {}
        for key, value in opportunity.constraint_updates.items():
            if key == "strategy":
                state.set_strategy(value)
            elif key == "priority":
                state.set_priority(value)
            else:
                state.update_constraint(key, value)
            applied[key] = value

        return applied

    def reassess(self, state: WorkflowSteeringState) -> OptimizationProposal | None:
        """Re-evaluate the state (called during execution to surface new opportunities).

        Bounded: only returns a proposal if the net value score is above 0.1.
        """
        proposal = self._recommender.propose(state)
        if proposal and proposal.evaluation and proposal.evaluation.net_value_score > 0.1:
            return proposal
        return None


__all__ = [
    "OptimizationAdvisor",
    # Components
    "ProactiveOptimizationEngine",
    "OptimizationScoringEngine",
    "OptimizationGovernancePolicy",
    "OperationalOptimizationRecommender",
    # Models
    "OptimizationOpportunity",
    "OptimizationProposal",
    "OptimizationEvaluation",
    "PolicyDecision",
    # Rendering
    "render_optimization_proposal",
    "render_optimization_summary",
    "render_optimization_evaluation",
]
