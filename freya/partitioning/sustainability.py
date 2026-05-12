"""freya/partitioning/sustainability.py

Operational Sustainability Cognition Engine.

Reasons about the long-term cost of stabilization strategies — detecting
adaptation fatigue, estimating stabilization sustainability, and preventing
organizational exhaustion over time.
"""
from __future__ import annotations

from freya.partitioning.models import (
    AdaptationFatigueRisk,
    OperationalPartition,
    OperationalSustainabilityAssessment,
    SustainabilityState,
)

# ---------------------------------------------------------------------------
# Fatigue signals: each maps an intervention name to fatigue contribution.
# ---------------------------------------------------------------------------
_FATIGUE_CONTRIBUTIONS: dict[str, float] = {
    "reasoning_compression":  0.35,
    "governance_batching":    0.25,
    "optimization_suspended": 0.30,
    "smoothing_applied":      0.20,
    "workflow_deferral":      0.20,
    "reservation_applied":    0.10,
    "batching_applied":       0.25,
}

# Per-partition-type fatigue multiplier when partition has been active "long".
_PARTITION_FATIGUE_MULTIPLIERS: dict[str, float] = {
    "incident_coordination": 1.30,
    "governance_escalation": 1.20,
    "retry_amplification":   1.15,
    "optimization_backlog":  1.10,
    "recovery_surge":        1.25,
    "standard":              1.00,
}

_FATIGUE_OUTLOOK: dict[str, str] = {
    "low":      "Stabilization strategy remains sustainable. No fatigue adjustment needed.",
    "moderate": "Moderate fatigue accumulating. Begin planning rotation of interventions to avoid exhaustion.",
    "high":     "High fatigue risk. Reduce intervention depth and introduce recovery intervals.",
    "critical": "Critical fatigue level. Immediate intervention rotation required — current strategy is unsustainable.",
}

_RECOVERY_SUSTAINABILITY: dict[SustainabilityState, str] = {
    "sustainable": "Recovery pacing sustainable at current velocity.",
    "at_risk":     "Recovery pacing sustainable short-term; medium-term rotation recommended.",
    "fatigued":    "Recovery pacing degrading due to fatigue — interventions losing effectiveness.",
    "exhausted":   "Recovery has stalled. Organizational capacity is exhausted. Escalate to human operator.",
}

_ORGANIZATIONAL_OUTLOOK: dict[SustainabilityState, str] = {
    "sustainable": "Organizational equilibrium on a positive trajectory. Continue current approach.",
    "at_risk":     "Organizational sustainability showing early stress. Introduce adaptive recovery pauses.",
    "fatigued":    "Organizational exhaustion risk elevated. Reduce intervention footprint immediately.",
    "exhausted":   "Organizational capacity critically depleted. Emergency recovery governance required.",
}


def _compute_fatigue_score(
    active_interventions: list[str],
    active_partitions: list[OperationalPartition],
    duration_cycles: int,
) -> float:
    """Compute a [0.0, 1.0] fatigue score from interventions, partitions, and duration."""
    base = sum(_FATIGUE_CONTRIBUTIONS.get(i, 0.10) for i in active_interventions)
    multiplier = 1.0
    for p in active_partitions:
        multiplier = max(multiplier, _PARTITION_FATIGUE_MULTIPLIERS.get(p.partition_type, 1.0))
    duration_factor = min(1.0 + (duration_cycles - 1) * 0.10, 2.5)
    return min(base * multiplier * duration_factor / 3.0, 1.0)


def _classify_fatigue(score: float) -> AdaptationFatigueRisk:
    if score >= 0.75:
        return "critical"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "moderate"
    return "low"


def _classify_sustainability(score: float) -> SustainabilityState:
    if score >= 0.75:
        return "exhausted"
    if score >= 0.55:
        return "fatigued"
    if score >= 0.35:
        return "at_risk"
    return "sustainable"


class OperationalSustainabilityEngine:
    """Assesses operational sustainability and adaptation fatigue over time."""

    def assess(
        self,
        active_interventions: list[str],
        active_partitions: list[OperationalPartition],
        duration_cycles: int = 1,
    ) -> OperationalSustainabilityAssessment:
        """Return a sustainability assessment for the current operational state.

        Args:
            active_interventions: Interventions currently applied.
            active_partitions: Currently active operational partitions.
            duration_cycles: Number of consecutive stabilization cycles
                             these interventions have been active.
        """
        score = _compute_fatigue_score(
            active_interventions, active_partitions, duration_cycles
        )
        fatigue = _classify_fatigue(score)
        state = _classify_sustainability(score)

        overloaded = [
            p.partition_name
            for p in active_partitions
            if p.stabilization_priority in ("critical", "high")
            and _PARTITION_FATIGUE_MULTIPLIERS.get(p.partition_type, 1.0) >= 1.20
        ]

        return OperationalSustainabilityAssessment(
            sustainability_state=state,
            adaptation_fatigue_risk=fatigue,
            overloaded_partitions=overloaded,
            recovery_sustainability=_RECOVERY_SUSTAINABILITY[state],
            organizational_outlook=_ORGANIZATIONAL_OUTLOOK[state],
        )

    def fatigue_breakdown(
        self, active_interventions: list[str]
    ) -> dict[str, float]:
        """Return per-intervention fatigue contributions for transparency."""
        return {
            i: _FATIGUE_CONTRIBUTIONS.get(i, 0.10)
            for i in active_interventions
        }
