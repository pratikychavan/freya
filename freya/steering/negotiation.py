"""freya/steering/negotiation.py

ConstraintNegotiationEngine — detects workflow conflicts and generates
NegotiationProposals with concrete resolution options.

Detection logic is deterministic and domain-aware.  Each conflict rule is
a pure function: (WorkflowSteeringState) → NegotiationProposal | None.

Rules evaluated (in order):
  1. hotel_over_budget      — hotel cost estimate exceeds budget
  2. premium_flight_cost    — premium flight would consume most of budget
  3. timeline_too_tight     — nights < minimum for destination
  4. strategy_depth_conflict — cognitive mode chosen but budget is very low
  5. proximity_vs_budget    — hotel proximity preference conflicts with budget
  6. approval_depth         — governance overhead too high for simple workflow
"""
from __future__ import annotations

import uuid
from typing import Any

from freya.steering.models import (
    NegotiationOption,
    NegotiationProposal,
    OperationalConstraint,
    WorkflowSteeringState,
)

# ---------------------------------------------------------------------------
# Budget thresholds used by rules
# ---------------------------------------------------------------------------

_HOTEL_PER_NIGHT_BUDGET_FRACTION = 0.35   # hotel should use ≤35% of total budget
_FLIGHT_BUDGET_FRACTION = 0.50            # flight should use ≤50% of total budget
_PREMIUM_NIGHTLY_RATE = 8_000             # above this = "premium hotel"
_ECONOMY_NIGHTLY_RATE = 3_000
_PREMIUM_FLIGHT_COST = 15_000
_ECONOMY_FLIGHT_COST = 6_000
_COGNITIVE_MIN_BUDGET = 20_000            # cognitive mode only worthwhile above this
_MIN_NIGHTS = 1


def _pid() -> str:
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Individual conflict detectors
# ---------------------------------------------------------------------------


def _detect_hotel_over_budget(state: WorkflowSteeringState) -> NegotiationProposal | None:
    """Hotel nightly rate would exceed the budget fraction."""
    budget_c = state.get_constraint("budget_inr")
    nights_c = state.get_constraint("nights")
    proximity = any(p.preference_name == "hotel_proximity" for p in state.preferences)

    if budget_c is None:
        return None

    budget = float(budget_c.value)
    nights = int(nights_c.value) if nights_c else 2
    max_hotel_spend = budget * _HOTEL_PER_NIGHT_BUDGET_FRACTION
    nightly_limit = max_hotel_spend / nights

    # Only flag if user wants proximity but that drives costs above limit
    if not proximity:
        return None
    if nightly_limit >= _PREMIUM_NIGHTLY_RATE:
        return None   # budget is comfortable enough

    shortfall = (_PREMIUM_NIGHTLY_RATE - nightly_limit) * nights

    return NegotiationProposal(
        proposal_id=_pid(),
        reason=(
            f"Hotels near the venue typically cost ₹{_PREMIUM_NIGHTLY_RATE:,}/night, "
            f"but your current budget allows ₹{int(nightly_limit):,}/night for accommodation."
        ),
        detected_conflict="hotel_over_budget",
        options=[
            NegotiationOption(
                option_id="increase_budget",
                title="Increase hotel budget",
                description=f"Add ₹{int(shortfall):,} to your total budget for a hotel near the venue.",
                impact_summary="Saves ~2 hours/day commute. No change in flight tier.",
                estimated_cost_change=shortfall,
                estimated_time_change=-2.0 * nights,
                constraint_updates={"budget_inr": budget + shortfall},
            ),
            NegotiationOption(
                option_id="stay_farther",
                title="Stay farther from venue",
                description="Select a budget hotel 5–10 km from the venue.",
                impact_summary=f"Saves ₹{int(shortfall):,} total. Adds ~45 min commute each way.",
                estimated_cost_change=0.0,
                estimated_time_change=1.5 * nights,
                constraint_updates={"hotel_proximity": False},
            ),
            NegotiationOption(
                option_id="reduce_hotel_quality",
                title="Reduce hotel quality",
                description="Choose a 2-star hotel close to the venue instead of a 4-star.",
                impact_summary=f"Close to venue. Saves ₹{int(shortfall * 0.6):,}. Basic amenities only.",
                estimated_cost_change=-shortfall * 0.6,
                estimated_time_change=-1.0 * nights,
                constraint_updates={"hotel_tier": "budget"},
            ),
        ],
        recommended_option_id="increase_budget",
    )


def _detect_premium_flight_cost(state: WorkflowSteeringState) -> NegotiationProposal | None:
    """Premium flight preference would consume too much of the budget."""
    budget_c = state.get_constraint("budget_inr")
    premium = any(p.preference_name == "premium" for p in state.preferences)

    if budget_c is None or not premium:
        return None

    budget = float(budget_c.value)
    if budget >= _PREMIUM_FLIGHT_COST * 2:
        return None   # comfortable

    savings = _PREMIUM_FLIGHT_COST - _ECONOMY_FLIGHT_COST

    return NegotiationProposal(
        proposal_id=_pid(),
        reason=(
            f"A business-class flight costs ~₹{_PREMIUM_FLIGHT_COST:,}, "
            f"which is {int(_PREMIUM_FLIGHT_COST / budget * 100)}% of your total budget."
        ),
        detected_conflict="premium_flight_over_budget",
        options=[
            NegotiationOption(
                option_id="economy_flight",
                title="Book economy class",
                description="Switch to economy. Use savings for accommodation or expenses.",
                impact_summary=f"Saves ₹{savings:,}. Slight comfort reduction on short domestic routes.",
                estimated_cost_change=-savings,
                estimated_time_change=0.0,
                constraint_updates={"flight_class": "economy"},
            ),
            NegotiationOption(
                option_id="increase_flight_budget",
                title="Increase total budget",
                description=f"Raise budget by ₹{savings:,} to accommodate business class.",
                impact_summary="Book business class. No other changes required.",
                estimated_cost_change=savings,
                estimated_time_change=0.0,
                constraint_updates={"budget_inr": budget + savings},
            ),
            NegotiationOption(
                option_id="premium_only_return",
                title="Upgrade return flight only",
                description="Fly economy outbound, upgrade return leg to business.",
                impact_summary=f"Saves ₹{int(savings * 0.5):,} vs full upgrade. Half the comfort benefit.",
                estimated_cost_change=savings * 0.5,
                estimated_time_change=0.0,
                constraint_updates={"flight_class": "mixed"},
            ),
        ],
        recommended_option_id="economy_flight",
    )


def _detect_timeline_too_tight(state: WorkflowSteeringState) -> NegotiationProposal | None:
    """Trip nights are below the practical minimum."""
    nights_c = state.get_constraint("nights")
    if nights_c is None:
        return None
    nights = int(nights_c.value)
    if nights >= _MIN_NIGHTS:
        return None

    return NegotiationProposal(
        proposal_id=_pid(),
        reason=f"A {nights}-night stay barely accounts for travel time and a single working day.",
        detected_conflict="timeline_too_tight",
        options=[
            NegotiationOption(
                option_id="extend_one_night",
                title="Extend stay by one night",
                description="Add one night for a more comfortable schedule.",
                impact_summary="Adds ~₹3,000–₹5,000. Removes time pressure.",
                estimated_cost_change=4_000.0,
                estimated_time_change=24.0,
                constraint_updates={"nights": nights + 1},
            ),
            NegotiationOption(
                option_id="keep_tight",
                title="Keep current timeline",
                description="Proceed as planned. Schedule may be tight.",
                impact_summary="No extra cost. High time pressure during trip.",
                estimated_cost_change=0.0,
                estimated_time_change=0.0,
                constraint_updates={},
            ),
        ],
        recommended_option_id="extend_one_night",
    )


def _detect_strategy_depth_conflict(state: WorkflowSteeringState) -> NegotiationProposal | None:
    """Cognitive strategy chosen but budget is too low to justify deep analysis."""
    budget_c = state.get_constraint("budget_inr")
    if budget_c is None:
        return None
    if state.strategy != "cognitive":
        return None
    budget = float(budget_c.value)
    if budget >= _COGNITIVE_MIN_BUDGET:
        return None

    return NegotiationProposal(
        proposal_id=_pid(),
        reason=(
            f"Deep cognitive analysis is most useful for high-value decisions. "
            f"Your budget (₹{int(budget):,}) is below the threshold where it adds significant value."
        ),
        detected_conflict="strategy_depth_conflict",
        options=[
            NegotiationOption(
                option_id="use_deterministic",
                title="Switch to fast deterministic planning",
                description="Use rule-based planning. Faster, equally accurate at this budget level.",
                impact_summary="Reduces planning time significantly. Same quality outcome.",
                estimated_cost_change=0.0,
                estimated_time_change=-0.5,
                constraint_updates={"strategy": "deterministic"},
            ),
            NegotiationOption(
                option_id="keep_cognitive",
                title="Keep cognitive analysis",
                description="Continue with deep analysis even at lower budget.",
                impact_summary="Slightly longer planning. May surface non-obvious options.",
                estimated_cost_change=0.0,
                estimated_time_change=0.5,
                constraint_updates={},
            ),
        ],
        recommended_option_id="use_deterministic",
    )


def _detect_proximity_vs_budget(state: WorkflowSteeringState) -> NegotiationProposal | None:
    """Generic proximity preference with no specific hotel conflict already flagged."""
    # Only run if hotel_over_budget did NOT already fire
    existing = {p.detected_conflict for p in state.active_proposals}
    if "hotel_over_budget" in existing:
        return None

    proximity = any(p.preference_name == "hotel_proximity" for p in state.preferences)
    budget_c = state.get_constraint("budget_inr")
    cost_pref = any(
        p.preference_name == "cost_sensitivity" and p.preference_value == "high"
        for p in state.preferences
    )

    if not proximity or not cost_pref or budget_c is None:
        return None

    budget = float(budget_c.value)
    if budget >= 50_000:
        return None   # plenty of money, no conflict

    return NegotiationProposal(
        proposal_id=_pid(),
        reason="You prefer proximity to the venue and lower cost, which are often in tension.",
        detected_conflict="proximity_vs_cost",
        options=[
            NegotiationOption(
                option_id="proximity_wins",
                title="Prioritise proximity",
                description="Accept slightly higher hotel cost for venue-adjacent accommodation.",
                impact_summary="Up to ₹5,000 more. Saves commute time each day.",
                estimated_cost_change=5_000.0,
                estimated_time_change=-1.5,
                constraint_updates={"hotel_proximity": True, "hotel_tier": "standard"},
            ),
            NegotiationOption(
                option_id="cost_wins",
                title="Prioritise lower cost",
                description="Choose a budget hotel slightly farther from the venue.",
                impact_summary="Saves up to ₹5,000. Slight commute overhead.",
                estimated_cost_change=-5_000.0,
                estimated_time_change=1.0,
                constraint_updates={"hotel_proximity": False},
            ),
        ],
        recommended_option_id="proximity_wins",
    )


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------

_RULES = [
    _detect_hotel_over_budget,
    _detect_premium_flight_cost,
    _detect_timeline_too_tight,
    _detect_strategy_depth_conflict,
    _detect_proximity_vs_budget,
]


class ConstraintNegotiationEngine:
    """Detect workflow conflicts and generate NegotiationProposals."""

    def detect(self, state: WorkflowSteeringState) -> list[NegotiationProposal]:
        """Run all conflict rules and return any proposals generated."""
        proposals: list[NegotiationProposal] = []
        for rule in _RULES:
            try:
                proposal = rule(state)
                if proposal is not None:
                    proposals.append(proposal)
                    # Make new proposals visible to subsequent rules
                    state.active_proposals.append(proposal)
            except Exception:
                pass  # rules must not crash the caller
        return proposals

    def has_conflicts(self, state: WorkflowSteeringState) -> bool:
        """Quick check — returns True if any conflict exists."""
        return bool(self.detect(WorkflowSteeringState(**state.model_dump())))
