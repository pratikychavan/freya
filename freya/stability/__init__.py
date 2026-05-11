"""freya/stability/__init__.py

Operational Stabilization + Adaptive Trust layer.

Usage
-----
    from freya.stability import OperationalStabilizationPipeline

    pipeline = OperationalStabilizationPipeline()
    result = pipeline.assess(
        workflow_id="wf-001",
        prior_guidance=[...],
        governance_history=[...],
        optimization_history=[...],
        active_constraints={...},
        active_preferences={...},
        compliant_streak=3,
    )
    print(pipeline.render(result))
"""
from __future__ import annotations

from freya.stability.drift import DriftAnalysis, OperationalDriftEngine
from freya.stability.friction import AdaptiveGovernanceFrictionEngine, FrictionProfile
from freya.stability.models import (
    AdaptiveTrustState,
    OperationalStabilityState,
    OperationalWeightProfile,
    StabilizationRecommendation,
)
from freya.stability.rendering import (
    render_stabilization_recommendation,
    render_stability_state,
    render_trust_state,
    render_weight_profile,
)
from freya.stability.stabilizer import OperationalStabilizer
from freya.stability.trust import AdaptiveTrustEngine
from freya.stability.weighting import OperationalPreferenceWeightingEngine

__all__ = [
    # Pipeline
    "OperationalStabilizationPipeline",
    # Engines
    "OperationalStabilizer",
    "AdaptiveTrustEngine",
    "AdaptiveGovernanceFrictionEngine",
    "OperationalPreferenceWeightingEngine",
    "OperationalDriftEngine",
    # Models
    "OperationalStabilityState",
    "AdaptiveTrustState",
    "OperationalWeightProfile",
    "StabilizationRecommendation",
    "DriftAnalysis",
    "FrictionProfile",
    # Renderers
    "render_stability_state",
    "render_trust_state",
    "render_stabilization_recommendation",
    "render_weight_profile",
]


class OperationalStabilizationPipeline:
    """Façade wiring all stabilization + trust components."""

    def __init__(self) -> None:
        self._stabilizer = OperationalStabilizer()
        self._trust      = AdaptiveTrustEngine()
        self._friction   = AdaptiveGovernanceFrictionEngine()
        self._weighting  = OperationalPreferenceWeightingEngine()
        self._drift      = OperationalDriftEngine()

    def assess(
        self,
        workflow_id: str,
        prior_guidance: list[str],
        governance_history: list[str],
        optimization_history: list[str],
        active_constraints: dict | None = None,
        active_preferences: dict | None = None,
        compliant_streak: int = 0,
    ) -> dict:
        """Run the full stabilization assessment.

        Returns a dict with keys:
          stability        OperationalStabilityState
          trust            AdaptiveTrustState
          friction         FrictionProfile
          weights          OperationalWeightProfile
          drift            DriftAnalysis
          recommendation   StabilizationRecommendation | None
          guidance_message str  (contextual stabilization message, may be empty)
        """
        active_constraints = active_constraints or {}
        active_preferences = active_preferences or {}

        # 1. Stability assessment
        stability = self._stabilizer.assess(workflow_id, prior_guidance)

        # 2. Trust state
        trust = self._trust.evaluate(workflow_id, governance_history, compliant_streak)

        # 3. Friction profile
        friction = self._friction.compute(stability, trust)

        # 4. Weight profile
        weights = self._weighting.build(active_constraints, active_preferences, prior_guidance)

        # 5. Drift analysis
        drift = self._drift.analyse(prior_guidance, governance_history, optimization_history)

        # 6. Stabilization recommendation
        recommendation = self._stabilizer.recommend(stability, prior_guidance)

        # 7. Contextual guidance message
        guidance_msg = self._stabilizer.contextual_guidance(stability, prior_guidance, recommendation)

        return {
            "stability":       stability,
            "trust":           trust,
            "friction":        friction,
            "weights":         weights,
            "drift":           drift,
            "recommendation":  recommendation,
            "guidance_message": guidance_msg,
        }

    def render(self, result: dict, *, full: bool = True) -> str:
        """Render a full stabilization assessment to a terminal string."""
        parts: list[str] = [
            render_stability_state(result["stability"]),
            render_trust_state(result["trust"]),
        ]
        if full:
            parts.append(render_weight_profile(result["weights"]))
        rec = result.get("recommendation")
        if rec is not None:
            parts.append(render_stabilization_recommendation(rec))
        return "\n".join(parts)

    def trust_engine(self) -> AdaptiveTrustEngine:
        return self._trust

    def friction_engine(self) -> AdaptiveGovernanceFrictionEngine:
        return self._friction
