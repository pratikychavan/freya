"""freya/context/history.py

WorkflowHistoryEngine — summarises workflow evolution into terse, auditable
operational statements.

Outputs feed into:
  - ContextualOperationalCognitionEngine (as steering context)
  - ContextualGovernanceEngine           (for pattern detection)
  - Human-centered rendering
"""
from __future__ import annotations

from freya.context.models import OperationalContext


class WorkflowHistoryEngine:
    """Distils raw history lists into structured operational summaries."""

    # ── Public API ────────────────────────────────────────────────────────────

    def summarize_guidance(self, ctx: OperationalContext) -> list[str]:
        """Return human-readable summaries of prior guidance patterns."""
        if not ctx.prior_guidance:
            return ["No prior guidance recorded."]
        summaries: list[str] = []
        for g in ctx.prior_guidance:
            summaries.append(f"User previously provided guidance: \"{g}\"")
        # Detect recurring tendencies
        summaries += self._detect_guidance_tendencies(ctx.prior_guidance)
        return summaries

    def summarize_optimizations(self, ctx: OperationalContext) -> list[str]:
        if not ctx.optimization_history:
            return ["No optimizations applied in this session."]
        summaries: list[str] = []
        for o in ctx.optimization_history:
            summaries.append(f"Optimization applied: {o}")
        summaries += self._detect_optimization_tendencies(ctx.optimization_history)
        return summaries

    def summarize_governance(self, ctx: OperationalContext) -> list[str]:
        if not ctx.governance_history:
            return ["Governance: no events recorded."]
        summaries: list[str] = []
        for g in ctx.governance_history:
            summaries.append(f"Governance event: {g}")
        summaries += self._detect_governance_patterns(ctx.governance_history)
        return summaries

    def full_summary(self, ctx: OperationalContext) -> list[str]:
        """All three summaries concatenated for use as reasoning context."""
        return (
            self.summarize_guidance(ctx)
            + self.summarize_optimizations(ctx)
            + self.summarize_governance(ctx)
        )

    def as_context_block(self, ctx: OperationalContext) -> str:
        """Return the full summary as a newline-separated string block."""
        return "\n".join(f"  - {line}" for line in self.full_summary(ctx))

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _detect_guidance_tendencies(guidance: list[str]) -> list[str]:
        tendencies: list[str] = []
        low_cost = sum(
            1 for g in guidance
            if any(kw in g.lower() for kw in ("cheaper", "cost", "budget", "affordable", "reduce"))
        )
        convenience = sum(
            1 for g in guidance
            if any(kw in g.lower() for kw in ("metro", "convenient", "proximity", "near", "close"))
        )
        speed = sum(
            1 for g in guidance
            if any(kw in g.lower() for kw in ("faster", "speed", "quick", "less time"))
        )
        quality = sum(
            1 for g in guidance
            if any(kw in g.lower() for kw in ("quality", "better", "premium", "high-end"))
        )

        if low_cost >= 2:
            tendencies.append("User consistently prioritised cost reduction.")
        if convenience >= 2:
            tendencies.append("User consistently prioritised location convenience.")
        if speed >= 2:
            tendencies.append("User consistently prioritised execution speed.")
        if quality >= 2:
            tendencies.append("User consistently prioritised output quality.")
        return tendencies

    @staticmethod
    def _detect_optimization_tendencies(history: list[str]) -> list[str]:
        out: list[str] = []
        cost_opts = sum(1 for h in history if "cost" in h.lower() or "cheap" in h.lower())
        if cost_opts >= 2:
            out.append(f"Workflow optimized for lower cost {cost_opts} time(s).")
        return out

    @staticmethod
    def _detect_governance_patterns(history: list[str]) -> list[str]:
        out: list[str] = []
        bypass_attempts = sum(
            1 for h in history
            if "bypass" in h.lower() or "skip" in h.lower() or "ignore" in h.lower()
        )
        if bypass_attempts >= 1:
            out.append(
                f"Governance: {bypass_attempts} bypass attempt(s) detected and blocked this session."
            )
        blocked = sum(1 for h in history if "blocked" in h.lower() or "denied" in h.lower())
        if blocked >= 2:
            out.append("Governance: multiple actions blocked — heightened scrutiny active.")
        return out
