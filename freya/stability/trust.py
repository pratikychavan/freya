"""freya/stability/trust.py

AdaptiveTrustEngine

Manages workflow-scoped operational trust.

Design rules:
  - Trust is workflow-scoped, not user-scoped
  - Trust is ALWAYS recoverable — no permanent distrust states
  - Scrutiny evolves with behavior, both directions
  - No personality profiling, no social scoring
"""
from __future__ import annotations

from freya.stability.models import (
    AdaptiveTrustState,
    GovernanceScrutiny,
    TrustLevel,
    TrustTrend,
)

# Scrutiny tier ordering (index = severity)
_SCRUTINY_ORDER: list[GovernanceScrutiny] = ["minimal", "standard", "elevated", "high", "maximum"]
_TRUST_ORDER:    list[TrustLevel]         = ["restricted", "cautious", "standard", "established"]

_BYPASS_KW = ("bypass", "skip", "ignore", "override", "disable", "circumvent")
_BLOCK_KW  = ("blocked", "denied", "rejected")


class AdaptiveTrustEngine:
    """Evolves governance trust based on workflow operational behaviour."""

    def evaluate(
        self,
        workflow_id: str,
        governance_history: list[str],
        compliant_streak: int = 0,
    ) -> AdaptiveTrustState:
        """Compute a fresh trust state from governance history."""
        bypass_count  = self._count_keywords(governance_history, _BYPASS_KW)
        blocked_count = self._count_keywords(governance_history, _BLOCK_KW)
        total_conflicts = bypass_count + blocked_count

        # Trust level
        trust = self._compute_trust(total_conflicts, compliant_streak)

        # Scrutiny level
        scrutiny = self._compute_scrutiny(total_conflicts, compliant_streak)

        # Trend
        trend = self._compute_trend(total_conflicts, compliant_streak)

        return AdaptiveTrustState(
            workflow_id=workflow_id,
            trust_level=trust,
            governance_scrutiny=scrutiny,
            recent_governance_events=governance_history[-5:],
            trust_trend=trend,
            compliant_action_streak=compliant_streak,
            total_bypass_attempts=bypass_count,
        )

    def apply_compliant_action(self, state: AdaptiveTrustState) -> AdaptiveTrustState:
        """Record a compliant action; potentially improve trust."""
        new_streak = state.compliant_action_streak + 1
        return self.evaluate(
            state.workflow_id,
            state.recent_governance_events,
            new_streak,
        )

    def apply_governance_conflict(
        self, state: AdaptiveTrustState, event: str
    ) -> AdaptiveTrustState:
        """Record a governance conflict; reduce trust accordingly."""
        updated_history = state.recent_governance_events + [event]
        return self.evaluate(
            state.workflow_id,
            updated_history,
            compliant_streak=0,   # streak resets on conflict
        )

    def describe_scrutiny(self, state: AdaptiveTrustState) -> str:
        """Return a one-line human-readable scrutiny explanation."""
        descriptions = {
            "minimal":  "Minimal friction — well-established workflow.",
            "standard": "Standard governance checks apply.",
            "elevated": "Elevated scrutiny — some prior governance conflicts.",
            "high":     "High scrutiny — multiple conflicts noted; confirm key actions.",
            "maximum":  "Maximum scrutiny — governance approval required for all actions.",
        }
        return descriptions.get(state.governance_scrutiny, "Standard scrutiny.")

    def recovery_message(self, state: AdaptiveTrustState) -> str | None:
        """Return a trust recovery hint when workflow is regaining trust."""
        if state.trust_trend != "improving":
            return None
        return (
            f"Trust is improving ({state.compliant_action_streak} compliant action(s) "
            "since last conflict). Governance friction is being reduced."
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _count_keywords(history: list[str], keywords: tuple) -> int:
        return sum(
            1 for h in history if any(kw in h.lower() for kw in keywords)
        )

    @staticmethod
    def _compute_trust(conflicts: int, streak: int) -> TrustLevel:
        # Recovery: every 3 compliant actions move up one level from the penalty floor
        recovery_bonus = streak // 3
        if conflicts == 0:
            level_idx = min(3, 2 + recovery_bonus)
        elif conflicts >= 4:
            level_idx = max(0, 0 + recovery_bonus)
        elif conflicts >= 2:
            level_idx = max(0, 1 + recovery_bonus)
        else:
            level_idx = max(0, 2 - 1 + recovery_bonus)
        level_idx = min(level_idx, 3)
        return _TRUST_ORDER[level_idx]

    @staticmethod
    def _compute_scrutiny(conflicts: int, streak: int) -> GovernanceScrutiny:
        # Recovery: every 3 compliant actions reduce scrutiny by 1 tier
        reduction = streak // 3
        if conflicts == 0:
            raw = 1  # standard
        elif conflicts >= 4:
            raw = 4  # maximum
        elif conflicts >= 3:
            raw = 3  # high
        elif conflicts >= 2:
            raw = 2  # elevated
        else:
            raw = 2  # elevated for first conflict
        adjusted = max(0, raw - reduction)
        return _SCRUTINY_ORDER[adjusted]

    @staticmethod
    def _compute_trend(conflicts: int, streak: int) -> TrustTrend:
        if streak >= 3 and conflicts > 0:
            return "improving"
        if conflicts == 0:
            return "stable"
        if streak == 0:
            return "declining"
        return "stable"
