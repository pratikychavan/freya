"""freya/optimization/recommendations.py

OperationalOptimizationRecommender — combines the engine, scoring, and policy
layers to produce final, human-centered OptimizationProposals.

This is the caller-facing façade for the optimization subsystem.

Usage::

    recommender = OperationalOptimizationRecommender()
    proposal = recommender.propose(state)
    if proposal:
        print(render_optimization_proposal(proposal))
"""
from __future__ import annotations

import uuid

from freya.optimization.engine import ProactiveOptimizationEngine
from freya.optimization.models import (
    OptimizationEvaluation,
    OptimizationOpportunity,
    OptimizationProposal,
)
from freya.optimization.policies import OptimizationGovernancePolicy
from freya.optimization.scoring import OptimizationScoringEngine
from freya.steering.models import WorkflowSteeringState


def _pid() -> str:
    return uuid.uuid4().hex[:8]


class OperationalOptimizationRecommender:
    """Full-stack recommendation pipeline: detect → score → filter → propose."""

    def __init__(self) -> None:
        self._engine = ProactiveOptimizationEngine()
        self._scorer = OptimizationScoringEngine()
        self._policy = OptimizationGovernancePolicy()

    def propose(
        self, state: WorkflowSteeringState
    ) -> OptimizationProposal | None:
        """Detect opportunities, score them, apply policy, return a proposal.

        Returns None if no actionable opportunities exist.
        """
        raw = self._engine.evaluate(state)
        if not raw:
            return None

        allowed, needs_approval, advisory = self._policy.filter(raw)

        # Rank within each tier
        allowed = self._scorer.rank(allowed)
        needs_approval = self._scorer.rank(needs_approval)

        all_actionable = allowed + needs_approval
        if not all_actionable and not advisory:
            return None

        evaluation = self._scorer.score(all_actionable or advisory)

        # Merge tiers into proposal — approval-required ones bubble to requires_approval
        requires_approval = bool(needs_approval)
        total_savings = sum(-(o.estimated_cost_delta or 0) for o in all_actionable)

        action_parts = []
        if total_savings > 0:
            action_parts.append(f"save up to ₹{int(total_savings):,}")
        time_total = sum(-(o.estimated_time_delta or 0) for o in all_actionable)
        if time_total > 0.3:
            action_parts.append(f"reduce planning time by ~{time_total:.1f} hr")
        action = (
            "Apply optimizations"
            + (f" — {', '.join(action_parts)}" if action_parts else "")
        )

        opportunities = all_actionable + advisory
        n = len(opportunities)
        reason = (
            f"Freya identified {n} optimization "
            f"{'opportunity' if n == 1 else 'opportunities'} for this workflow."
        )

        proposal = OptimizationProposal(
            proposal_id=_pid(),
            reason=reason,
            opportunities=opportunities,
            recommended_action=action,
            requires_approval=requires_approval,
            evaluation=evaluation,
        )
        return proposal

    def top_opportunity(
        self, state: WorkflowSteeringState
    ) -> OptimizationOpportunity | None:
        """Return only the single highest-value opportunity."""
        raw = self._engine.evaluate(state)
        if not raw:
            return None
        ranked = self._scorer.rank(raw)
        return ranked[0] if ranked else None

    def evaluate_only(self, state: WorkflowSteeringState) -> OptimizationEvaluation:
        """Score the current state without generating a full proposal."""
        opps = self._engine.evaluate(state)
        return self._scorer.score(opps)
