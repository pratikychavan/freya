"""freya/resilience/portfolio.py

Adaptation Portfolio Balancing Engine.

Assesses the strategic balance of active stabilization techniques,
detects overuse of individual strategies, and recommends rotation
to prevent adaptation monoculture.
"""
from __future__ import annotations

from freya.resilience.models import AdaptationPortfolioState, RotationBalance


_OVERUSE_THRESHOLD = 5          # cycles before a strategy is considered overused
_MONOCULTURE_FRACTION = 0.60    # fraction of total cycles that makes it monoculture
_SKEWED_RATIO = 2.0             # if one strategy > SKEWED_RATIO * avg, it's skewed


def _rotation_balance(
    usage_counts: dict[str, int],
) -> RotationBalance:
    if not usage_counts:
        return "balanced"
    values = list(usage_counts.values())
    total = sum(values)
    if total == 0:
        return "balanced"
    max_val = max(values)
    avg = total / len(values)
    # Monoculture: one strategy dominates > 60% of total usage
    if max_val / total >= _MONOCULTURE_FRACTION:
        return "monoculture"
    # Skewed: dominant strategy is > 2× the average
    if len(values) > 1 and max_val >= avg * _SKEWED_RATIO:
        return "skewed"
    return "balanced"


def _overused(usage_counts: dict[str, int]) -> list[str]:
    return [k for k, v in usage_counts.items() if v >= _OVERUSE_THRESHOLD]


def _sustainability_score(
    balance: RotationBalance,
    overused: list[str],
    strategy_count: int,
) -> float:
    """Compute a [0.0, 1.0] sustainability score.

    Higher = more sustainable portfolio.
    """
    score = 1.0
    if balance == "monoculture":
        score -= 0.50
    elif balance == "skewed":
        score -= 0.25
    # Each overused strategy reduces sustainability
    score -= len(overused) * 0.12
    # Single-strategy portfolio is inherently less sustainable
    if strategy_count == 1:
        score -= 0.15
    return round(max(0.0, min(1.0, score)), 2)


# Rotation recommendations keyed by overused strategies
_ROTATION_GUIDES: dict[str, str] = {
    "compression":         "Rotate compression → batching or reservation for 2+ cycles.",
    "batching":            "Reduce batching window; alternate with sequencing or smoothing.",
    "smoothing":           "Replace smoothing with transparent interventions (batching, reservation).",
    "governance_review":   "Defer low-priority reviews; batch critical ones into priority windows.",
    "reservation":         "Release non-critical reservations; shift to batching or sequencing.",
    "recovery_sequencing": "Introduce alternate recovery path; rotate primary/secondary each 3 cycles.",
}


class AdaptationPortfolioBalancingEngine:
    """Evaluates the strategic balance of the active stabilization portfolio."""

    def assess(
        self,
        active_strategies: list[str],
        usage_counts: dict[str, int],
    ) -> AdaptationPortfolioState:
        """Return an AdaptationPortfolioState for the current strategy set.

        Parameters
        ----------
        active_strategies:
            Currently active stabilization strategy names.
        usage_counts:
            Mapping of strategy name → cumulative cycle count.
        """
        overused = _overused(usage_counts)
        balance = _rotation_balance(usage_counts)
        score = _sustainability_score(balance, overused, len(active_strategies))

        return AdaptationPortfolioState(
            active_strategies=list(active_strategies),
            rotation_balance=balance,
            overused_strategies=overused,
            sustainability_score=score,
        )

    def recommend_rotation(
        self, portfolio: AdaptationPortfolioState
    ) -> str:
        """Return a human-readable rotation recommendation."""
        if not portfolio.overused_strategies and portfolio.rotation_balance == "balanced":
            return (
                "Portfolio balance is healthy. Continue current rotation. "
                "Monitor usage counts for early skew signals."
            )
        lines: list[str] = []
        if portfolio.rotation_balance == "monoculture":
            lines.append(
                "MONOCULTURE DETECTED: Adaptation strategy diversity is critical. "
                "Immediately introduce at least one alternate technique."
            )
        elif portfolio.rotation_balance == "skewed":
            lines.append("Portfolio is skewed. Reduce dominant strategy usage by at least 30%.")
        for strategy in portfolio.overused_strategies:
            guide = _ROTATION_GUIDES.get(strategy)
            if guide:
                lines.append(f"{strategy.upper()}: {guide}")
        return " ".join(lines) if lines else "Review portfolio balance before next cycle."
