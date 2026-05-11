"""freya/steering/recommendations.py

OperationalRecommendationEngine — proactively surfaces optimisation
opportunities based on the current WorkflowSteeringState.

Recommendations are independent of conflict detection: they fire when no
conflict exists but a better tradeoff is available.

Each recommendation is a dataclass with:
  rec_id          — short slug
  headline        — one-line action headline
  rationale       — why it's worthwhile
  impact_summary  — concrete numbers/outcomes
  priority        — "high" | "medium" | "low"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from freya.steering.models import WorkflowSteeringState

# ---------------------------------------------------------------------------
# Recommendation data type
# ---------------------------------------------------------------------------


@dataclass
class OperationalRecommendation:
    rec_id: str
    headline: str
    rationale: str
    impact_summary: str
    priority: Literal["high", "medium", "low"] = "medium"
    suggested_action: str = ""   # short label for the action the user can take


# ---------------------------------------------------------------------------
# Individual recommendation generators
# ---------------------------------------------------------------------------


def _rec_hotel_upgrade(state: WorkflowSteeringState) -> OperationalRecommendation | None:
    """Recommend a hotel upgrade when the budget easily supports it."""
    budget_c = state.get_constraint("budget_inr")
    nights_c = state.get_constraint("nights")
    proximity = any(p.preference_name == "hotel_proximity" for p in state.preferences)

    if not proximity or budget_c is None:
        return None

    budget = float(budget_c.value)
    nights = int(nights_c.value) if nights_c else 2

    # Only recommend if we have meaningful headroom
    premium_cost = 8_000 * nights
    if budget * 0.35 < premium_cost * 0.8:
        return None   # budget already tight

    savings_in_commute_hrs = 2.0 * nights

    return OperationalRecommendation(
        rec_id="hotel_upgrade",
        headline="Upgrade to a venue-adjacent hotel",
        rationale=f"Your budget comfortably supports a higher-tier hotel near the venue.",
        impact_summary=(
            f"Adds ~₹{int(premium_cost * 0.3):,} vs the default option. "
            f"Saves ~{savings_in_commute_hrs:.0f} hours of commute over the trip."
        ),
        priority="high",
        suggested_action="Allocate more hotel budget",
    )


def _rec_skip_deep_compare(state: WorkflowSteeringState) -> OperationalRecommendation | None:
    """Recommend skipping deep hotel comparison when budget is low and dates are tight."""
    budget_c = state.get_constraint("budget_inr")
    nights_c = state.get_constraint("nights")

    if budget_c is None:
        return None

    budget = float(budget_c.value)
    nights = int(nights_c.value) if nights_c else 2

    if budget > 30_000 or nights > 2:
        return None   # deep compare worthwhile

    return OperationalRecommendation(
        rec_id="skip_deep_compare",
        headline="Skip deep hotel comparison",
        rationale="For short, budget-conscious trips the top-rated nearby option is usually optimal.",
        impact_summary="Reduces planning time by ~40%. Quality impact is minimal at this budget tier.",
        priority="medium",
        suggested_action="Use fast hotel selection",
    )


def _rec_early_flight(state: WorkflowSteeringState) -> OperationalRecommendation | None:
    """Recommend booking the earliest available flight for more working time."""
    speed_pref = next(
        (p for p in state.preferences if p.preference_name == "speed"), None
    )
    if speed_pref and speed_pref.preference_value == "preferred":
        return OperationalRecommendation(
            rec_id="early_flight",
            headline="Book the earliest available outbound flight",
            rationale="An early departure gives you a full working day at the destination.",
            impact_summary="Gains ~4–6 hours of productive time on day 1. No additional cost.",
            priority="medium",
            suggested_action="Filter flights departing before 09:00",
        )
    return None


def _rec_bundle_savings(state: WorkflowSteeringState) -> OperationalRecommendation | None:
    """Suggest flight + hotel bundle when budget is above threshold."""
    budget_c = state.get_constraint("budget_inr")
    nights_c = state.get_constraint("nights")

    if budget_c is None:
        return None

    budget = float(budget_c.value)
    nights = int(nights_c.value) if nights_c else 1

    if budget < 25_000 or nights < 2:
        return None

    savings = int(budget * 0.07)

    return OperationalRecommendation(
        rec_id="bundle_savings",
        headline="Bundle flight + hotel for potential savings",
        rationale="Bundled bookings typically offer 5–10% discounts on the combined price.",
        impact_summary=f"Estimated saving: ₹{savings:,}. Simplifies expense reporting.",
        priority="low",
        suggested_action="Search bundled packages",
    )


def _rec_governance_simplify(state: WorkflowSteeringState) -> OperationalRecommendation | None:
    """Suggest reducing governance overhead when steering changes made budget compliant."""
    budget_c = state.get_constraint("budget_inr")
    if budget_c is None:
        return None

    budget = float(budget_c.value)
    if budget > 30_000:
        return None   # governance is appropriate

    has_approval_req = "manager_approval_required" in [
        d.applied_updates.get("governance") for d in state.decisions_made
    ]
    if not has_approval_req:
        return None

    return OperationalRecommendation(
        rec_id="governance_simplify",
        headline="Budget is within auto-approval threshold",
        rationale=f"At ₹{int(budget):,}, this trip qualifies for automatic approval.",
        impact_summary="Removes the manual approval step. Workflow runs without interruption.",
        priority="low",
        suggested_action="Remove manual approval checkpoint",
    )


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------

_GENERATORS = [
    _rec_hotel_upgrade,
    _rec_skip_deep_compare,
    _rec_early_flight,
    _rec_bundle_savings,
    _rec_governance_simplify,
]


class OperationalRecommendationEngine:
    """Generate proactive operational recommendations for a WorkflowSteeringState."""

    def recommend(self, state: WorkflowSteeringState) -> list[OperationalRecommendation]:
        """Return all applicable recommendations, sorted by priority."""
        results: list[OperationalRecommendation] = []
        for gen in _GENERATORS:
            try:
                rec = gen(state)
                if rec:
                    results.append(rec)
            except Exception:
                pass

        priority_order = {"high": 0, "medium": 1, "low": 2}
        results.sort(key=lambda r: priority_order.get(r.priority, 9))
        return results

    def top(self, state: WorkflowSteeringState, n: int = 1) -> list[OperationalRecommendation]:
        """Return the top-n recommendations."""
        return self.recommend(state)[:n]
