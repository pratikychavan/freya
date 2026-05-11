"""freya/stability/friction.py

AdaptiveGovernanceFrictionEngine

Dynamically adjusts governance friction based on workflow stability + trust.

Design rules:
  - Stable workflows → fewer interruptions
  - Unstable workflows → more confirmation prompts
  - No permanent high-friction states
  - Always collaborative, never punitive
"""
from __future__ import annotations

from typing import NamedTuple

from freya.stability.models import AdaptiveTrustState, OperationalStabilityState


class FrictionProfile(NamedTuple):
    """Current friction settings for a workflow."""
    clarification_rate: str    # "low" | "normal" | "high"
    approval_required:  bool
    confirmation_gates: str    # "minimal" | "standard" | "frequent"
    auto_apply_threshold: float  # confidence threshold below which clarification fires
    rationale: str


class AdaptiveGovernanceFrictionEngine:
    """Computes governance friction level from stability + trust state."""

    def compute(
        self,
        stability: OperationalStabilityState,
        trust: AdaptiveTrustState,
    ) -> FrictionProfile:
        """Return a FrictionProfile for the current workflow state."""
        scrutiny = trust.governance_scrutiny
        drift    = stability.drift_level

        # ── Maximum scrutiny overrides everything ─────────────────────────────
        if scrutiny == "maximum":
            return FrictionProfile(
                clarification_rate="high",
                approval_required=True,
                confirmation_gates="frequent",
                auto_apply_threshold=1.1,   # never auto-apply
                rationale=(
                    "Maximum governance scrutiny active — all actions require explicit approval."
                ),
            )

        # ── Severe drift → high friction regardless of trust ──────────────────
        if drift == "severe":
            return FrictionProfile(
                clarification_rate="high",
                approval_required=scrutiny in ("high", "maximum"),
                confirmation_gates="frequent",
                auto_apply_threshold=0.90,
                rationale=(
                    "Severe operational drift detected — additional confirmation required "
                    "to stabilize the workflow."
                ),
            )

        # ── High scrutiny or moderate drift → elevated friction ───────────────
        if scrutiny == "high" or drift == "moderate":
            return FrictionProfile(
                clarification_rate="normal",
                approval_required=False,
                confirmation_gates="standard",
                auto_apply_threshold=0.78,
                rationale=(
                    f"Elevated friction: scrutiny={scrutiny}, drift={drift}. "
                    "Key decisions will require confirmation."
                ),
            )

        # ── Established trust + no/mild drift → low friction ─────────────────
        if trust.trust_level == "established" and drift in ("none", "mild"):
            return FrictionProfile(
                clarification_rate="low",
                approval_required=False,
                confirmation_gates="minimal",
                auto_apply_threshold=0.60,
                rationale=(
                    "Well-established workflow with stable trajectory — friction minimized."
                ),
            )

        # ── Default: standard friction ────────────────────────────────────────
        return FrictionProfile(
            clarification_rate="normal",
            approval_required=False,
            confirmation_gates="standard",
            auto_apply_threshold=0.72,
            rationale="Standard governance friction for current workflow state.",
        )

    def should_clarify(
        self,
        confidence: float,
        profile: FrictionProfile,
    ) -> bool:
        """Return True when confidence falls below the auto-apply threshold."""
        return confidence < profile.auto_apply_threshold

    def friction_summary(self, profile: FrictionProfile) -> str:
        """One-line summary of current friction level."""
        if profile.clarification_rate == "low":
            return "Low friction — smooth approvals, minimal interruptions."
        if profile.clarification_rate == "high":
            return "High friction — frequent confirmation required."
        return "Standard friction — normal governance checks apply."
