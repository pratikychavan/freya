"""freya/context/preferences.py

ContextualPreferenceEngine

Infers recurring operational tendencies from workflow history.

This is OPERATIONAL PREFERENCE COGNITION — not personality profiling,
not conversational memory.  Every inference is tied to concrete workflow events.
"""
from __future__ import annotations

from freya.context.models import OperationalContext


class InferredPreferences:
    """Structured result of preference inference."""

    def __init__(
        self,
        dominant_priority: str,
        cost_orientation: str,
        governance_comfort: str,
        analysis_depth: str,
        location_sensitivity: bool,
        premium_acceptance: str,
        notes: list[str],
    ) -> None:
        self.dominant_priority    = dominant_priority    # "cost" | "speed" | "quality" | "convenience" | "balanced"
        self.cost_orientation     = cost_orientation     # "cost_averse" | "cost_neutral" | "premium_accepting"
        self.governance_comfort   = governance_comfort   # "friction_averse" | "standard" | "governance_accepting"
        self.analysis_depth       = analysis_depth       # "shallow" | "standard" | "deep"
        self.location_sensitivity = location_sensitivity # True if repeatedly uses location guidance
        self.premium_acceptance   = premium_acceptance   # "rejects" | "neutral" | "accepts"
        self.notes                = notes                # one-line reasoning strings

    def as_dict(self) -> dict:
        return {
            "dominant_priority":    self.dominant_priority,
            "cost_orientation":     self.cost_orientation,
            "governance_comfort":   self.governance_comfort,
            "analysis_depth":       self.analysis_depth,
            "location_sensitivity": self.location_sensitivity,
            "premium_acceptance":   self.premium_acceptance,
        }


_COST_KW    = ("cheaper", "cost", "budget", "save", "affordable", "reduce")
_SPEED_KW   = ("faster", "speed", "quick", "less time")
_QUALITY_KW = ("quality", "better", "premium", "improve")
_CONV_KW    = ("metro", "proximity", "near", "close", "convenient")
_PREMIUM_KW = ("premium", "luxury", "upgrade", "first class", "best")
_BYPASS_KW  = ("skip", "bypass", "ignore", "disable")


class ContextualPreferenceEngine:
    """Infers operational preferences from workflow history."""

    def infer(self, ctx: OperationalContext) -> InferredPreferences:
        all_guidance = ctx.prior_guidance
        notes: list[str] = []

        dominant = self._dominant_priority(all_guidance, notes)
        cost_ori = self._cost_orientation(all_guidance, notes)
        gov_comfort = self._governance_comfort(ctx, notes)
        depth = self._analysis_depth(ctx, notes)
        loc_sen = self._location_sensitivity(ctx, notes)
        premium = self._premium_acceptance(all_guidance, ctx, notes)

        return InferredPreferences(
            dominant_priority=dominant,
            cost_orientation=cost_ori,
            governance_comfort=gov_comfort,
            analysis_depth=depth,
            location_sensitivity=loc_sen,
            premium_acceptance=premium,
            notes=notes,
        )

    # ── Private inference methods ─────────────────────────────────────────────

    @staticmethod
    def _dominant_priority(guidance: list[str], notes: list[str]) -> str:
        text = " ".join(guidance).lower()
        scores = {
            "cost":       sum(text.count(k) for k in _COST_KW),
            "speed":      sum(text.count(k) for k in _SPEED_KW),
            "quality":    sum(text.count(k) for k in _QUALITY_KW),
            "convenience": sum(text.count(k) for k in _CONV_KW),
        }
        top = max(scores, key=lambda k: scores[k])
        top_val = scores[top]
        if top_val == 0:
            return "balanced"
        # If two categories are close, call it balanced
        sorted_vals = sorted(scores.values(), reverse=True)
        if len(sorted_vals) >= 2 and sorted_vals[1] >= sorted_vals[0] * 0.75:
            notes.append("Mixed priority signals detected — marked as balanced.")
            return "balanced"
        notes.append(f"User primarily guided toward '{top}' ({top_val} references).")
        return top

    @staticmethod
    def _cost_orientation(guidance: list[str], notes: list[str]) -> str:
        text = " ".join(guidance).lower()
        cost_hits    = sum(text.count(k) for k in _COST_KW)
        premium_hits = sum(text.count(k) for k in _PREMIUM_KW)
        if cost_hits >= 2 and cost_hits > premium_hits:
            notes.append("Repeated cost-reduction guidance — classified as cost_averse.")
            return "cost_averse"
        if premium_hits >= 2:
            notes.append("User accepted or requested premium options — premium_accepting.")
            return "premium_accepting"
        return "cost_neutral"

    @staticmethod
    def _governance_comfort(ctx: OperationalContext, notes: list[str]) -> str:
        bypass_attempts = sum(
            1 for g in ctx.governance_history
            if any(k in g.lower() for k in _BYPASS_KW)
        )
        if bypass_attempts >= 2:
            notes.append(f"{bypass_attempts} bypass attempts suggest governance friction aversion.")
            return "friction_averse"
        if bypass_attempts == 1:
            notes.append("One bypass attempt noted.")
            return "friction_averse"
        return "standard"

    @staticmethod
    def _analysis_depth(ctx: OperationalContext, notes: list[str]) -> str:
        depth = ctx.active_constraints.get("analysis_depth")
        if depth == "reduced":
            notes.append("Active constraint: analysis_depth=reduced.")
            return "shallow"
        if depth == "deep":
            notes.append("Active constraint: analysis_depth=deep.")
            return "deep"
        return "standard"

    @staticmethod
    def _location_sensitivity(ctx: OperationalContext, notes: list[str]) -> bool:
        location_hits = sum(
            1 for g in ctx.prior_guidance
            if any(k in g.lower() for k in _CONV_KW)
        )
        if location_hits >= 2 or ctx.active_preferences.get("metro_access"):
            notes.append("Recurring location guidance — location_sensitivity=True.")
            return True
        return False

    @staticmethod
    def _premium_acceptance(guidance: list[str], ctx: OperationalContext, notes: list[str]) -> str:
        text = " ".join(guidance).lower()
        premium_hits = sum(text.count(k) for k in _PREMIUM_KW)
        cost_hits    = sum(text.count(k) for k in _COST_KW)
        if premium_hits >= 2 and premium_hits > cost_hits:
            notes.append("Consistently accepts premium — marked 'accepts'.")
            return "accepts"
        if cost_hits >= 2:
            return "rejects"
        return "neutral"
