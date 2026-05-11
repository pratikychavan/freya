"""freya/context/trajectory.py

OperationalTrajectoryEngine

Tracks how a workflow is evolving over time:
  - Optimization direction (cost-down, quality-up, mixed, etc.)
  - Governance pattern (clean, conflicted, escalating)
  - Execution drift (changing priorities repeatedly)
  - Operational instability detection
"""
from __future__ import annotations

from freya.context.models import DriftSeverity, OperationalContext, OperationalTrajectory

_COST_KW    = ("cost", "cheap", "budget", "save", "reduce", "affordable")
_QUALITY_KW = ("quality", "better", "premium", "improve", "higher")
_SPEED_KW   = ("speed", "faster", "quick", "time", "rapid")
_CONV_KW    = ("metro", "convenient", "proximity", "near", "close", "access")


class OperationalTrajectoryEngine:
    """Computes and evaluates the operational trajectory of a workflow."""

    def compute(self, ctx: OperationalContext) -> OperationalTrajectory:
        direction = self._infer_optimization_direction(ctx)
        gov_pattern = self._infer_governance_pattern(ctx)
        drift = self._detect_drift(ctx)

        return OperationalTrajectory(
            trajectory_id=ctx.workflow_id,
            prior_decisions=list(ctx.prior_guidance[-10:]),  # last 10 steering decisions
            optimization_direction=direction,
            governance_pattern=gov_pattern,
            execution_drift=drift if drift != "none" else None,
        )

    def detect_instability(self, ctx: OperationalContext) -> list[str]:
        """Return a list of instability warnings (empty = stable)."""
        warnings: list[str] = []

        # Priority oscillation: switching between cost ↔ quality ↔ speed repeatedly
        osc = self._count_oscillation(ctx.prior_guidance)
        if osc >= 3:
            warnings.append(
                f"Optimization oscillation detected ({osc} priority reversals). "
                "Workflow direction is unstable — consider committing to a direction."
            )

        # Governance conflicts escalating
        blocked = sum(
            1 for g in ctx.governance_history
            if "blocked" in g.lower() or "denied" in g.lower()
        )
        if blocked >= 3:
            warnings.append(
                f"Escalating governance conflicts ({blocked} blocked actions). "
                "Review your guidance to align with governance policy."
            )

        # Repeated priority reversals
        reversals = self._count_priority_reversals(ctx.prior_guidance)
        if reversals >= 2:
            warnings.append(
                f"{reversals} priority reversals detected. "
                "Consistent operational steering improves execution quality."
            )

        return warnings

    def drift_severity(self, ctx: OperationalContext) -> DriftSeverity:
        raw = self._detect_drift(ctx)
        return raw  # type: ignore

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _infer_optimization_direction(ctx: OperationalContext) -> str:
        all_text = " ".join(ctx.optimization_history + ctx.prior_guidance).lower()
        cost_score    = sum(all_text.count(kw) for kw in _COST_KW)
        quality_score = sum(all_text.count(kw) for kw in _QUALITY_KW)
        speed_score   = sum(all_text.count(kw) for kw in _SPEED_KW)
        conv_score    = sum(all_text.count(kw) for kw in _CONV_KW)

        scores = {
            "cost_reduction":   cost_score,
            "quality_focus":    quality_score,
            "speed_focus":      speed_score,
            "convenience_focus": conv_score,
        }
        top = max(scores, key=lambda k: scores[k])
        top_val = scores[top]
        if top_val == 0:
            return "stable"
        # Check for mixed signals
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) >= 2 and sorted_scores[1] >= sorted_scores[0] * 0.7:
            return "mixed"
        return top

    @staticmethod
    def _infer_governance_pattern(ctx: OperationalContext) -> str:
        if not ctx.governance_history:
            return "clean"
        bypass = sum(1 for g in ctx.governance_history if "bypass" in g.lower())
        blocked = sum(1 for g in ctx.governance_history if "blocked" in g.lower())
        if bypass >= 2 or blocked >= 3:
            return "escalating_conflicts"
        if bypass >= 1 or blocked >= 1:
            return "minor_conflicts"
        return "clean"

    @staticmethod
    def _detect_drift(ctx: OperationalContext) -> DriftSeverity:
        reversals = OperationalTrajectoryEngine._count_priority_reversals(ctx.prior_guidance)
        if reversals >= 4:
            return "severe"
        if reversals >= 2:
            return "moderate"
        if reversals >= 1:
            return "mild"
        return "none"

    @staticmethod
    def _count_oscillation(guidance: list[str]) -> int:
        """Count direction changes in a guidance sequence."""
        if len(guidance) < 2:
            return 0
        directions: list[str] = []
        for g in guidance:
            lower = g.lower()
            if any(k in lower for k in _COST_KW):
                directions.append("cost")
            elif any(k in lower for k in _QUALITY_KW):
                directions.append("quality")
            elif any(k in lower for k in _SPEED_KW):
                directions.append("speed")
            elif any(k in lower for k in _CONV_KW):
                directions.append("convenience")
        changes = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i - 1])
        return changes

    @staticmethod
    def _count_priority_reversals(guidance: list[str]) -> int:
        """Count back-and-forth reversals (cost→quality→cost = 2)."""
        return OperationalTrajectoryEngine._count_oscillation(guidance)
