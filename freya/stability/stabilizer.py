"""freya/stability/stabilizer.py

OperationalStabilizer

Detects unstable workflow patterns and recommends stabilization modes.
Guides — never forcibly locks — workflow direction.
"""
from __future__ import annotations

from freya.stability.models import (
    OperationalMode,
    OperationalStabilityState,
    StabilizationRecommendation,
)

# ── Keyword banks ─────────────────────────────────────────────────────────────
_COST_KW    = ("cost", "cheap", "budget", "save", "affordable", "reduce")
_SPEED_KW   = ("speed", "faster", "quick", "rapid", "time")
_QUALITY_KW = ("quality", "better", "improve", "premium", "higher")
_CONV_KW    = ("metro", "convenient", "proximity", "near", "close", "access")

_RISK_ORDER = ["none", "low", "medium", "high", "critical"]

_MODE_LABELS: dict[OperationalMode, str] = {
    "cost_optimization":    "Cost Optimization",
    "balanced":             "Balanced Mode",
    "quality_optimization": "Quality Optimization",
    "speed_optimization":   "Speed Optimization",
    "governance_safe":      "Governance-Safe Mode",
    "unknown":              "Unknown",
}


class OperationalStabilizer:
    """Analyses guidance history and produces stabilization assessments."""

    # ── Public API ────────────────────────────────────────────────────────────

    def assess(self, workflow_id: str, prior_guidance: list[str]) -> OperationalStabilityState:
        """Compute a stability snapshot from guidance history."""
        reversals = self._count_reversals(prior_guidance)
        drift = self._drift_level(reversals)
        score = self._stability_score(reversals, len(prior_guidance))
        mode  = self._dominant_mode(prior_guidance)

        return OperationalStabilityState(
            workflow_id=workflow_id,
            stability_score=round(score, 2),
            drift_level=drift,
            reversal_count=reversals,
            active_operational_mode=mode,
            stabilization_recommended=reversals >= 2 or score < 0.55,
        )

    def recommend(
        self,
        state: OperationalStabilityState,
        prior_guidance: list[str],
    ) -> StabilizationRecommendation | None:
        """Return a collaborative stabilization recommendation or None if stable."""
        if not state.stabilization_recommended:
            return None

        # Determine best stabilization target from guidance pattern
        target = self._recommend_mode(prior_guidance, state)
        history_summary = self._summarize_pattern(prior_guidance)

        return StabilizationRecommendation(
            title="Operational Stability Recommendation",
            reason=(
                f"You've changed priorities {state.reversal_count} time(s) during execution. "
                f"Current pattern: {history_summary}. "
                f"Stabilizing will reduce replanning cycles and execution drift."
            ),
            recommended_mode=target,
            expected_impact=(
                "Fewer replanning cycles, lower execution drift, "
                "smoother optimization trajectory."
            ),
            options=[
                "Cost Optimization — minimize total cost",
                "Balanced Mode — balance cost, speed, and quality",
                "Quality Optimization — prioritize output quality",
                "Speed Optimization — minimize execution time",
                "Governance-Safe Mode — maximize compliance",
            ],
        )

    def contextual_guidance(
        self,
        state: OperationalStabilityState,
        prior_guidance: list[str],
        recommendation: StabilizationRecommendation | None,
    ) -> str:
        """Generate a concise contextual stabilization message."""
        if not state.stabilization_recommended or recommendation is None:
            return ""
        pattern = self._summarize_pattern(prior_guidance)
        mode_label = _MODE_LABELS.get(recommendation.recommended_mode, "Balanced Mode")
        return (
            f"You've adjusted priorities several times during execution.\n"
            f"  Pattern detected: {pattern}\n"
            f"  Would you like to stabilize into {mode_label}?\n"
            f"  This will reduce oscillation and improve execution coherence."
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _direction(text: str) -> str | None:
        lower = text.lower()
        if any(k in lower for k in _COST_KW):
            return "cost"
        if any(k in lower for k in _SPEED_KW):
            return "speed"
        if any(k in lower for k in _QUALITY_KW):
            return "quality"
        if any(k in lower for k in _CONV_KW):
            return "convenience"
        return None

    @classmethod
    def _count_reversals(cls, guidance: list[str]) -> int:
        directions = [d for g in guidance if (d := cls._direction(g)) is not None]
        return sum(1 for i in range(1, len(directions)) if directions[i] != directions[i - 1])

    @staticmethod
    def _drift_level(reversals: int) -> str:
        if reversals >= 4:
            return "severe"
        if reversals >= 2:
            return "moderate"
        if reversals >= 1:
            return "mild"
        return "none"

    @staticmethod
    def _stability_score(reversals: int, total: int) -> float:
        if total == 0:
            return 1.0
        raw = max(0.0, 1.0 - (reversals / max(total, 1)) * 1.5)
        return min(1.0, max(0.0, raw))

    @classmethod
    def _dominant_mode(cls, guidance: list[str]) -> OperationalMode:
        counts: dict[str, int] = {"cost": 0, "speed": 0, "quality": 0, "convenience": 0}
        for g in guidance:
            d = cls._direction(g)
            if d:
                counts[d] = counts.get(d, 0) + 1
        top = max(counts, key=lambda k: counts[k])
        if counts[top] == 0:
            return "balanced"
        mapping = {
            "cost":        "cost_optimization",
            "speed":       "speed_optimization",
            "quality":     "quality_optimization",
            "convenience": "balanced",
        }
        return mapping.get(top, "balanced")  # type: ignore

    @classmethod
    def _recommend_mode(
        cls, guidance: list[str], state: OperationalStabilityState
    ) -> OperationalMode:
        # If there's a clear dominant direction, recommend it
        dom = cls._dominant_mode(guidance)
        # If severely oscillating, recommend balanced regardless
        if state.drift_level == "severe":
            return "balanced"
        return dom

    @classmethod
    def _summarize_pattern(cls, guidance: list[str]) -> str:
        directions = [d for g in guidance if (d := cls._direction(g)) is not None]
        if not directions:
            return "no clear pattern"
        # Show last 5 transitions
        shown = directions[-5:]
        return " → ".join(shown)
