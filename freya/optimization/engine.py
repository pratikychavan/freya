"""freya/optimization/engine.py

ProactiveOptimizationEngine — inspects a WorkflowSteeringState and
continuously surfaces OptimizationProposals.

CRITICAL: The engine RECOMMENDS; it never auto-applies.
Each proposal requires explicit user acceptance before any state mutation.

Detection rules (evaluated in order):
  1. cost_hotel_alternative    — cheaper hotel option exists
  2. cognitive_strategy_spend  — cognitive mode used but budget/complexity is low
  3. delegation_depth          — unnecessary child-workflow depth
  4. governance_overhead       — approval chains longer than needed
  5. retry_depth_excess        — recovery retry budget disproportionate
  6. planning_latency          — deterministic plan would be faster with no quality loss
"""
from __future__ import annotations

import uuid
from typing import Any

from freya.optimization.models import (
    OptimizationOpportunity,
    OptimizationProposal,
)
from freya.steering.models import WorkflowSteeringState

# ---------------------------------------------------------------------------
# Per-rule helpers
# ---------------------------------------------------------------------------

_PREMIUM_HOTEL_RATE = 8_000          # INR/night — typical near-venue premium hotel
_BUDGET_HOTEL_RATE = 3_500           # INR/night — budget alternative
_COGNITIVE_BUDGET_THRESHOLD = 20_000 # below this, cognitive adds little value
_MAX_SENSIBLE_RETRY_DEPTH = 3
_HIGH_DELEGATION_COUNT = 4           # child workflows above this is unusual


def _pid() -> str:
    return uuid.uuid4().hex[:8]


def _detect_cost_hotel_alternative(
    state: WorkflowSteeringState,
) -> OptimizationOpportunity | None:
    """Surface a cheaper hotel option when budget is tight and proximity isn't mandatory."""
    budget_c = state.get_constraint("budget_inr")
    nights_c = state.get_constraint("nights")
    proximity_required = any(
        p.preference_name == "hotel_proximity" and p.preference_value == "preferred"
        for p in state.preferences
    )
    if budget_c is None or proximity_required:
        return None

    budget = float(budget_c.value)
    nights = int(nights_c.value) if nights_c else 2
    hotel_budget = budget * 0.35
    nightly = hotel_budget / nights

    if nightly <= _BUDGET_HOTEL_RATE:
        return None   # already in budget range

    savings = (_PREMIUM_HOTEL_RATE - _BUDGET_HOTEL_RATE) * nights

    return OptimizationOpportunity(
        opportunity_id=_pid(),
        title="Lower-cost hotel option available",
        description=(
            f"A budget-tier hotel is available at ~₹{_BUDGET_HOTEL_RATE:,}/night, "
            f"saving ₹{int(savings):,} over {nights} nights."
        ),
        optimization_type="cost",
        estimated_cost_delta=-savings,
        estimated_time_delta=0.5 * nights,   # slight commute overhead
        estimated_quality_delta=-0.1,
        confidence_score=0.88,
        governance_impact="no_change",
        constraint_updates={"hotel_tier": "budget"},
    )


def _detect_cognitive_strategy_spend(
    state: WorkflowSteeringState,
) -> OptimizationOpportunity | None:
    """Recommend switching away from cognitive mode when it's overkill."""
    if state.strategy != "cognitive":
        return None
    budget_c = state.get_constraint("budget_inr")
    if budget_c is None:
        return None
    budget = float(budget_c.value)
    if budget >= _COGNITIVE_BUDGET_THRESHOLD:
        return None   # cognitive mode is justified

    return OptimizationOpportunity(
        opportunity_id=_pid(),
        title="Switch to faster planning mode",
        description=(
            "Cognitive analysis is enabled but the workflow budget is below the threshold "
            "where deep reasoning adds measurable value."
        ),
        optimization_type="cognitive",
        estimated_cost_delta=-budget * 0.05,   # ~5% reduction in LLM cost
        estimated_time_delta=-0.5,
        estimated_quality_delta=-0.05,
        confidence_score=0.82,
        governance_impact="no_change",
        constraint_updates={"strategy": "deterministic"},
    )


def _detect_delegation_depth(
    state: WorkflowSteeringState,
) -> OptimizationOpportunity | None:
    """Flag when delegation depth exceeds practical benefit."""
    depth_c = state.get_constraint("delegation_depth")
    if depth_c is None:
        return None
    depth = int(depth_c.value)
    if depth <= _HIGH_DELEGATION_COUNT:
        return None

    reduction = depth - 2

    return OptimizationOpportunity(
        opportunity_id=_pid(),
        title="Reduce workflow delegation depth",
        description=(
            f"Delegation depth is {depth}. Reducing to 2 removes redundant "
            "sub-workflow layers with no functional impact."
        ),
        optimization_type="delegation",
        estimated_cost_delta=-reduction * 500.0,   # overhead per layer
        estimated_time_delta=-reduction * 0.25,
        estimated_quality_delta=0.0,
        confidence_score=0.79,
        governance_impact="no_change",
        constraint_updates={"delegation_depth": 2},
    )


def _detect_governance_overhead(
    state: WorkflowSteeringState,
) -> OptimizationOpportunity | None:
    """Suggest removing manual approval when budget is within auto-approval range."""
    budget_c = state.get_constraint("budget_inr")
    approval_c = state.get_constraint("require_manual_approval")
    if budget_c is None or approval_c is None:
        return None
    if not bool(approval_c.value):
        return None   # no approval requirement

    budget = float(budget_c.value)
    if budget > 30_000:
        return None   # approval is justified

    return OptimizationOpportunity(
        opportunity_id=_pid(),
        title="Streamline approval process",
        description=(
            f"Budget (₹{int(budget):,}) is within the auto-approval threshold. "
            "Manual approval is unnecessary and adds delay."
        ),
        optimization_type="governance",
        estimated_cost_delta=0.0,
        estimated_time_delta=-2.0,   # removes manual review wait
        estimated_quality_delta=0.0,
        confidence_score=0.91,
        governance_impact="requires_approval",   # ironic but correct — removing approval needs one sign-off
        constraint_updates={"require_manual_approval": False},
    )


def _detect_retry_depth_excess(
    state: WorkflowSteeringState,
) -> OptimizationOpportunity | None:
    """Recommend lowering recovery retry budget when it's disproportionate."""
    retry_c = state.get_constraint("max_retries")
    if retry_c is None:
        return None
    retries = int(retry_c.value)
    if retries <= _MAX_SENSIBLE_RETRY_DEPTH:
        return None

    return OptimizationOpportunity(
        opportunity_id=_pid(),
        title="Reduce recovery retry depth",
        description=(
            f"Max retries is set to {retries}. Reducing to {_MAX_SENSIBLE_RETRY_DEPTH} "
            "is sufficient for most transient failures and avoids runaway cost."
        ),
        optimization_type="cost",
        estimated_cost_delta=-(retries - _MAX_SENSIBLE_RETRY_DEPTH) * 200.0,
        estimated_time_delta=-(retries - _MAX_SENSIBLE_RETRY_DEPTH) * 0.1,
        estimated_quality_delta=-0.02,
        confidence_score=0.76,
        governance_impact="no_change",
        constraint_updates={"max_retries": _MAX_SENSIBLE_RETRY_DEPTH},
    )


def _detect_planning_latency(
    state: WorkflowSteeringState,
) -> OptimizationOpportunity | None:
    """Recommend deterministic planning for simple, low-budget workflows."""
    if state.strategy == "deterministic":
        return None
    budget_c = state.get_constraint("budget_inr")
    nights_c = state.get_constraint("nights")
    if budget_c is None:
        return None
    budget = float(budget_c.value)
    nights = int(nights_c.value) if nights_c else 2
    if budget > 40_000 or nights > 3:
        return None   # complex enough to warrant deeper planning

    return OptimizationOpportunity(
        opportunity_id=_pid(),
        title="Use fast deterministic planning",
        description=(
            "For this workflow's complexity level, deterministic planning "
            "produces equivalent results with significantly lower latency."
        ),
        optimization_type="speed",
        estimated_cost_delta=-budget * 0.04,
        estimated_time_delta=-0.3,
        estimated_quality_delta=0.0,
        confidence_score=0.85,
        governance_impact="no_change",
        constraint_updates={"strategy": "deterministic"},
    )


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------

_RULES = [
    _detect_cost_hotel_alternative,
    _detect_cognitive_strategy_spend,
    _detect_delegation_depth,
    _detect_governance_overhead,
    _detect_retry_depth_excess,
    _detect_planning_latency,
]


class ProactiveOptimizationEngine:
    """Inspect a WorkflowSteeringState and surface OptimizationProposals.

    NEVER auto-applies; always returns proposals for user review.
    """

    def evaluate(self, state: WorkflowSteeringState) -> list[OptimizationOpportunity]:
        """Run all rules and return detected opportunities."""
        opportunities: list[OptimizationOpportunity] = []
        for rule in _RULES:
            try:
                opp = rule(state)
                if opp is not None:
                    opportunities.append(opp)
            except Exception:
                pass
        return opportunities

    def build_proposal(
        self,
        state: WorkflowSteeringState,
        opportunities: list[OptimizationOpportunity] | None = None,
    ) -> OptimizationProposal | None:
        """Evaluate the state and return a single proposal bundling all opportunities."""
        opps = opportunities if opportunities is not None else self.evaluate(state)
        if not opps:
            return None

        requires_approval = any(
            o.governance_impact == "requires_approval" for o in opps
        )
        total_savings = sum(
            -(o.estimated_cost_delta or 0) for o in opps
        )
        action = (
            f"Apply {len(opps)} optimization{'s' if len(opps) > 1 else ''}"
            + (f" — save up to ₹{int(total_savings):,}" if total_savings > 0 else "")
        )

        return OptimizationProposal(
            proposal_id=_pid(),
            reason=(
                f"Freya identified {len(opps)} optimization "
                f"{'opportunities' if len(opps) > 1 else 'opportunity'} "
                "for this workflow."
            ),
            opportunities=opps,
            recommended_action=action,
            requires_approval=requires_approval,
        )

    def reassess(self, state: WorkflowSteeringState) -> list[OptimizationOpportunity]:
        """Re-evaluate the state (called periodically during execution).

        Returns only newly discovered opportunities not already surfaced.
        Bounded to prevent optimization spam.
        """
        current_ids = {p.proposal_id for p in state.active_proposals}  # type: ignore[attr-defined]
        return self.evaluate(state)
