"""freya/stability/drift.py

OperationalDriftEngine

Detects optimization oscillation, execution drift, and operational instability.
Recommends stabilization without blocking collaboration.
"""
from __future__ import annotations

from freya.stability.models import DriftLevel, OperationalStabilityState

_COST_KW    = ("cost", "cheap", "budget", "save", "affordable", "reduce")
_SPEED_KW   = ("speed", "faster", "quick", "rapid", "time")
_QUALITY_KW = ("quality", "better", "improve", "premium", "higher")
_CONV_KW    = ("metro", "convenient", "proximity", "near", "close", "access")


def _direction_of(text: str) -> str | None:
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


class DriftAnalysis:
    """Result of a drift analysis."""

    def __init__(
        self,
        drift_level: DriftLevel,
        reversal_count: int,
        oscillation_loops: int,
        direction_sequence: list[str],
        governance_conflicts: int,
        warnings: list[str],
        thrashing: bool,
    ) -> None:
        self.drift_level         = drift_level
        self.reversal_count      = reversal_count
        self.oscillation_loops   = oscillation_loops
        self.direction_sequence  = direction_sequence
        self.governance_conflicts= governance_conflicts
        self.warnings            = warnings
        self.thrashing           = thrashing

    def is_stable(self) -> bool:
        return self.drift_level == "none" and not self.thrashing


class OperationalDriftEngine:
    """Primary drift and oscillation detection engine."""

    def analyse(
        self,
        prior_guidance: list[str],
        governance_history: list[str],
        optimization_history: list[str],
    ) -> DriftAnalysis:
        directions   = [d for g in prior_guidance if (d := _direction_of(g)) is not None]
        reversals    = self._count_reversals(directions)
        loops        = self._count_oscillation_loops(directions)
        gov_conflicts= self._count_governance_conflicts(governance_history)
        thrashing    = self._detect_thrashing(optimization_history)

        drift_level  = self._drift_level(reversals, gov_conflicts, thrashing)
        warnings     = self._build_warnings(
            drift_level, reversals, loops, gov_conflicts, thrashing, directions
        )

        return DriftAnalysis(
            drift_level=drift_level,
            reversal_count=reversals,
            oscillation_loops=loops,
            direction_sequence=directions,
            governance_conflicts=gov_conflicts,
            warnings=warnings,
            thrashing=thrashing,
        )

    def stability_score(self, analysis: DriftAnalysis, total_guidance: int) -> float:
        """Compute 0.0–1.0 stability score from a DriftAnalysis."""
        if total_guidance == 0:
            return 1.0
        penalty = (
            analysis.reversal_count * 0.12
            + analysis.governance_conflicts * 0.15
            + (0.20 if analysis.thrashing else 0.0)
        )
        return round(max(0.0, min(1.0, 1.0 - penalty)), 2)

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _count_reversals(directions: list[str]) -> int:
        return sum(1 for i in range(1, len(directions)) if directions[i] != directions[i - 1])

    @staticmethod
    def _count_oscillation_loops(directions: list[str]) -> int:
        """Count A→B→A cycles."""
        if len(directions) < 3:
            return 0
        loops = 0
        for i in range(len(directions) - 2):
            if directions[i] == directions[i + 2] and directions[i] != directions[i + 1]:
                loops += 1
        return loops

    @staticmethod
    def _count_governance_conflicts(history: list[str]) -> int:
        return sum(
            1 for h in history
            if any(kw in h.lower() for kw in ("blocked", "denied", "bypass", "rejected"))
        )

    @staticmethod
    def _detect_thrashing(optimization_history: list[str]) -> bool:
        """Thrashing = undo-redo cycles in optimization history."""
        if len(optimization_history) < 3:
            return False
        # Simple heuristic: same type of optimization reversed within 3 entries
        for i in range(len(optimization_history) - 2):
            a = optimization_history[i].lower()
            b = optimization_history[i + 2].lower()
            if a == b:
                return True
        return False

    @staticmethod
    def _drift_level(
        reversals: int, gov_conflicts: int, thrashing: bool
    ) -> DriftLevel:
        score = reversals + gov_conflicts * 1.5 + (2 if thrashing else 0)
        if score >= 6:
            return "severe"
        if score >= 3:
            return "moderate"
        if score >= 1:
            return "mild"
        return "none"

    @staticmethod
    def _build_warnings(
        drift: DriftLevel,
        reversals: int,
        loops: int,
        conflicts: int,
        thrashing: bool,
        directions: list[str],
    ) -> list[str]:
        warnings: list[str] = []
        if reversals >= 3:
            shown = directions[-6:]
            pattern = " → ".join(shown)
            warnings.append(
                f"Optimization oscillation: {reversals} priority reversals detected. "
                f"Pattern: {pattern}"
            )
        if loops >= 2:
            warnings.append(
                f"{loops} oscillation loop(s) detected (A→B→A cycles). "
                "Consider committing to a stable direction."
            )
        if conflicts >= 2:
            warnings.append(
                f"{conflicts} governance conflict(s) recorded. "
                "Heightened scrutiny is active."
            )
        if thrashing:
            warnings.append(
                "Optimization thrashing detected — the same optimization was reversed "
                "within a short window. Consider stabilizing the workflow."
            )
        if drift == "severe":
            warnings.append(
                "Severe operational drift. Stabilization strongly recommended "
                "to maintain execution coherence."
            )
        return warnings
