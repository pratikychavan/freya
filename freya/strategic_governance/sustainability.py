"""freya/strategic_governance/sustainability.py

Governance Sustainability Cognition Engine.

Detects governance process overload, forecasts review-path exhaustion,
and recommends adjustments before governance continuity degrades.
Preserves governance as a functioning organizational capability —
not merely a compliance requirement.
"""
from __future__ import annotations

from freya.strategic_governance.models import (
    EscalationSaturationRisk,
    GovernanceCapacityState,
    GovernanceSustainabilityState,
    ReviewPressure,
    SustainabilityOutlook,
)


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
_REVIEW_PRESSURE_BANDS: list[tuple[float, ReviewPressure]] = [
    (0.40, "low"),
    (0.60, "moderate"),
    (0.80, "high"),
    (1.01, "critical"),
]

_ESCALATION_RISK_BANDS: list[tuple[float, EscalationSaturationRisk]] = [
    (0.45, "low"),
    (0.65, "moderate"),
    (0.80, "high"),
    (1.01, "critical"),
]

_CAPACITY_STATE_MAP: dict[tuple[ReviewPressure, EscalationSaturationRisk], GovernanceCapacityState] = {
    ("low",    "low"):      "healthy",
    ("low",    "moderate"): "healthy",
    ("moderate","low"):     "healthy",
    ("moderate","moderate"):"strained",
    ("moderate","high"):    "strained",
    ("high",   "low"):      "strained",
    ("high",   "moderate"): "saturated",
    ("high",   "high"):     "saturated",
    ("critical","low"):     "saturated",
    ("critical","moderate"):"critical",
    ("critical","high"):    "critical",
    ("critical","critical"):"critical",
    ("low",    "critical"): "saturated",
    ("moderate","critical"):"critical",
    ("high",   "critical"): "critical",
}

_OUTLOOK_MAP: dict[GovernanceCapacityState, SustainabilityOutlook] = {
    "healthy":   "sustainable",
    "strained":  "at_risk",
    "saturated": "degrading",
    "critical":  "unsustainable",
}

_ADJUSTMENTS: dict[GovernanceCapacityState, str] = {
    "healthy": (
        "Governance process is healthy. Continue routine review cadence. "
        "Monitor escalation queue for early load signals."
    ),
    "strained": (
        "Governance capacity is strained. Redistribute low-priority reviews to async channels. "
        "Reduce concurrent escalation paths and pre-position review board capacity."
    ),
    "saturated": (
        "Governance process is saturated. Immediately implement review batching for "
        "non-critical items. Reserve escalation slots for Severity-1 decisions. "
        "Defer audit-class reviews by 1 cycle if operationally safe."
    ),
    "critical": (
        "CRITICAL: Governance process is at collapse risk. Emergency review redistribution "
        "required. Activate governance delegation protocol. Executive escalation is mandatory "
        "before any new governance-requiring decisions are initiated."
    ),
}


def _pressure_band(load: float, bands: list[tuple[float, str]]) -> str:
    for cutoff, label in bands:
        if load < cutoff:
            return label
    return bands[-1][1]


class GovernanceSustainabilityCognitionEngine:
    """Assesses the sustainability of governance processes under load."""

    def assess(
        self,
        review_load: float,
        escalation_load: float,
        confidence: float = 0.70,
    ) -> GovernanceSustainabilityState:
        """Return a GovernanceSustainabilityState for the current governance loads.

        Parameters
        ----------
        review_load:
            Normalized review queue pressure [0.0, 1.0].
        escalation_load:
            Normalized escalation queue saturation risk [0.0, 1.0].
        confidence:
            Analytical confidence — low confidence applies conservative thresholds.
        """
        # Low confidence → inflate loads conservatively
        if confidence < 0.55:
            review_load = min(1.0, review_load + 0.08)
            escalation_load = min(1.0, escalation_load + 0.08)

        review_pressure: ReviewPressure = _pressure_band(review_load, _REVIEW_PRESSURE_BANDS)
        escalation_risk: EscalationSaturationRisk = _pressure_band(
            escalation_load, _ESCALATION_RISK_BANDS
        )

        capacity_state = _CAPACITY_STATE_MAP.get(
            (review_pressure, escalation_risk), "strained"
        )
        outlook = _OUTLOOK_MAP[capacity_state]
        adjustment = _ADJUSTMENTS[capacity_state]

        return GovernanceSustainabilityState(
            governance_capacity_state=capacity_state,
            review_pressure=review_pressure,
            escalation_saturation_risk=escalation_risk,
            sustainability_outlook=outlook,
            recommended_adjustment=adjustment,
        )
