"""freya/context/governance.py

ContextualGovernanceEngine

Applies governance rules contextually — scrutiny is adjusted based on
the workflow's governance history and the current operational trajectory.

Design rules:
  - Bypass attempts are ALWAYS blocked (hard rule, no context adjustment)
  - Repeated risky behaviour increases scrutiny dynamically
  - Trusted patterns (clean history) can reduce friction
  - All decisions are auditable
"""
from __future__ import annotations

from typing import NamedTuple

from freya.context.models import GovernanceRisk, OperationalContext


class ContextualGovernanceDecision(NamedTuple):
    allowed: bool
    risk_level: GovernanceRisk
    reason: str
    scrutiny_level: str        # "standard" | "elevated" | "high" | "maximum"
    escalation_required: bool


_BYPASS_SIGNALS = (
    "skip approval", "bypass review", "ignore governance", "skip governance",
    "disable approval", "override governance", "bypass approval",
    "skip checks", "ignore rules", "skip the review", "disable governance",
    "ignore the approval", "skip review", "skip validation",
)


class ContextualGovernanceEngine:
    """Evaluates governance decisions with historical context awareness."""

    def evaluate(
        self,
        raw_input: str,
        ctx: OperationalContext,
    ) -> ContextualGovernanceDecision:
        lower = raw_input.lower()

        # ── HARD RULE: bypass is always blocked ──────────────────────────────
        if any(sig in lower for sig in _BYPASS_SIGNALS):
            self._record(ctx, f"Governance bypass attempt BLOCKED: \"{raw_input[:80]}\"")
            return ContextualGovernanceDecision(
                allowed=False,
                risk_level="critical",
                reason=(
                    "Governance bypass is not permitted. "
                    "All bypass and skip requests are unconditionally rejected."
                ),
                scrutiny_level="maximum",
                escalation_required=True,
            )

        # ── Compute scrutiny from history ─────────────────────────────────────
        scrutiny = self._compute_scrutiny(ctx)
        bypass_count = sum(
            1 for g in ctx.governance_history
            if "bypass" in g.lower() or "blocked" in g.lower()
        )

        # ── Under maximum scrutiny: require explicit approval ─────────────────
        if scrutiny == "maximum":
            return ContextualGovernanceDecision(
                allowed=False,
                risk_level="high",
                reason=(
                    f"Workflow has {bypass_count} governance conflict(s). "
                    "All actions require explicit governance approval."
                ),
                scrutiny_level="maximum",
                escalation_required=True,
            )

        # ── High scrutiny: allow with warning ────────────────────────────────
        if scrutiny == "high":
            return ContextualGovernanceDecision(
                allowed=True,
                risk_level="medium",
                reason=(
                    "Action allowed under elevated governance scrutiny due to "
                    "prior conflicts in this workflow."
                ),
                scrutiny_level="high",
                escalation_required=False,
            )

        # ── Detect risky optimization patterns ───────────────────────────────
        risk = self._assess_risk(raw_input, ctx)
        if risk in ("high", "critical"):
            return ContextualGovernanceDecision(
                allowed=False,
                risk_level=risk,
                reason=(
                    "Potentially risky operation detected given current workflow state. "
                    "Governance review required."
                ),
                scrutiny_level=scrutiny,
                escalation_required=True,
            )

        # ── Default: allowed ──────────────────────────────────────────────────
        return ContextualGovernanceDecision(
            allowed=True,
            risk_level=risk,
            reason="Action is within governance bounds for current workflow state.",
            scrutiny_level=scrutiny,
            escalation_required=False,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _compute_scrutiny(ctx: OperationalContext) -> str:
        bypass_count = sum(
            1 for g in ctx.governance_history
            if "bypass" in g.lower() or "blocked" in g.lower()
        )
        blocked_count = sum(
            1 for g in ctx.governance_history
            if "denied" in g.lower() or "blocked" in g.lower()
        )
        total_alerts = bypass_count + blocked_count
        if total_alerts >= 4:
            return "maximum"
        if total_alerts >= 2:
            return "high"
        if total_alerts >= 1:
            return "elevated"
        return "standard"

    @staticmethod
    def _assess_risk(raw: str, ctx: OperationalContext) -> GovernanceRisk:
        lower = raw.lower()
        # Rapid policy changes in quick succession
        policy_change = any(
            kw in lower for kw in ("disable", "override", "remove constraint", "drop approval")
        )
        if policy_change:
            return "high"
        # Cost escalation when already cost-sensitive
        if ctx.operational_mode == "cost_sensitive" and any(
            kw in lower for kw in ("premium", "upgrade", "expensive")
        ):
            return "medium"
        return "low"

    @staticmethod
    def _record(ctx: OperationalContext, entry: str) -> None:
        # Context is immutable (Pydantic model); callers should persist via store.
        # This is a no-op here; the store.record_governance_event is the persister.
        pass
