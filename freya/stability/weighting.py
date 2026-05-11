"""freya/stability/weighting.py

OperationalPreferenceWeightingEngine

Distinguishes hard constraints from soft constraints, assigns numeric weights
to preference dimensions, and produces a hierarchical OperationalWeightProfile.
"""
from __future__ import annotations

from freya.stability.models import OperationalWeightProfile

# ── Hard constraint indicators ────────────────────────────────────────────────
_HARD_KEYS = {
    "budget_inr",
    "budget_ceiling",
    "max_budget",
    "governance_rules",
    "compliance_required",
    "max_retries",
}

# ── Soft constraint indicators ─────────────────────────────────────────────────
_SOFT_KEYS = {
    "metro_access",
    "hotel_proximity",
    "near_venue",
    "premium",
    "hotel_tier",
    "seating_class",
}

# ── Default weights per operational dimension ─────────────────────────────────
_DEFAULT_WEIGHTS = {
    "cost":        0.5,
    "speed":       0.5,
    "quality":     0.5,
    "convenience": 0.5,
    "governance":  1.0,   # governance weight is always maximum
}

_COST_KW    = ("cost", "cheap", "budget", "save", "affordable", "reduce")
_SPEED_KW   = ("speed", "faster", "quick", "rapid")
_QUALITY_KW = ("quality", "better", "improve", "premium", "higher")
_CONV_KW    = ("metro", "convenient", "proximity", "near", "close", "access")


class OperationalPreferenceWeightingEngine:
    """Builds weighted preference profiles from constraint + guidance data."""

    def build(
        self,
        active_constraints: dict,
        active_preferences: dict,
        prior_guidance: list[str],
    ) -> OperationalWeightProfile:
        hard, soft = self._classify_constraints(active_constraints, active_preferences)
        weights    = self._compute_weights(active_preferences, prior_guidance)
        priorities = self._priority_order(weights)

        return OperationalWeightProfile(
            hard_constraints=hard,
            soft_constraints=soft,
            weighted_preferences=weights,
            operational_priorities=priorities,
        )

    def explain(self, profile: OperationalWeightProfile) -> list[str]:
        """Return human-readable explanation lines for the weight profile."""
        lines: list[str] = []
        if profile.hard_constraints:
            lines.append("Hard constraints (non-negotiable):")
            for k, v in profile.hard_constraints.items():
                lines.append(f"  • {k.replace('_',' ').title()}: {v}")
        if profile.soft_constraints:
            lines.append("Soft constraints (tradeable):")
            for k, v in profile.soft_constraints.items():
                lines.append(f"  • {k.replace('_',' ').title()}: {v}")
        if profile.weighted_preferences:
            lines.append("Preference weights (0.0 – 1.0):")
            for dim, w in sorted(
                profile.weighted_preferences.items(), key=lambda x: -x[1]
            ):
                bar = "█" * int(w * 10) + "░" * (10 - int(w * 10))
                lines.append(f"  • {dim:<15} {bar}  {w:.1f}")
        if profile.operational_priorities:
            lines.append(f"Priority order: {' > '.join(profile.operational_priorities)}")
        return lines

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _classify_constraints(
        constraints: dict, preferences: dict
    ) -> tuple[dict, dict]:
        hard: dict = {}
        soft: dict = {}
        all_items = {**constraints, **preferences}
        for k, v in all_items.items():
            if k in _HARD_KEYS or "budget" in k.lower() or "ceiling" in k.lower():
                hard[k] = v
            else:
                soft[k] = v
        return hard, soft

    @classmethod
    def _compute_weights(cls, preferences: dict, guidance: list[str]) -> dict:
        weights = dict(_DEFAULT_WEIGHTS)

        # Boost weights based on preferences dict
        if preferences.get("metro_access") or preferences.get("hotel_proximity"):
            weights["convenience"] = min(1.0, weights["convenience"] + 0.2)
        if preferences.get("cost_sensitivity") == "high":
            weights["cost"] = min(1.0, weights["cost"] + 0.3)
        if preferences.get("premium"):
            weights["quality"] = min(1.0, weights["quality"] + 0.2)
        if preferences.get("speed") == "preferred":
            weights["speed"] = min(1.0, weights["speed"] + 0.2)

        # Boost from guidance history frequency
        text = " ".join(guidance).lower()
        cost_hits = sum(text.count(k) for k in _COST_KW)
        speed_hits = sum(text.count(k) for k in _SPEED_KW)
        quality_hits = sum(text.count(k) for k in _QUALITY_KW)
        conv_hits  = sum(text.count(k) for k in _CONV_KW)

        total = max(cost_hits + speed_hits + quality_hits + conv_hits, 1)
        weights["cost"]        = round(min(1.0, weights["cost"]        + cost_hits    / total * 0.3), 2)
        weights["speed"]       = round(min(1.0, weights["speed"]       + speed_hits   / total * 0.3), 2)
        weights["quality"]     = round(min(1.0, weights["quality"]     + quality_hits / total * 0.3), 2)
        weights["convenience"] = round(min(1.0, weights["convenience"] + conv_hits    / total * 0.3), 2)

        return weights

    @staticmethod
    def _priority_order(weights: dict) -> list[str]:
        dims = {k: v for k, v in weights.items() if k != "governance"}
        ordered = sorted(dims.keys(), key=lambda k: -dims[k])
        return ordered
