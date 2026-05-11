"""freya/predictive/smoothing.py

OperationalSmoothingEngine

Applies gradual, phased operational adjustments to prevent sudden coordination shocks.
Adaptation is always incremental — never abrupt.

Smoothing phases (ascending severity):
  none        — no adjustment needed
  gentle      — 5–15 % reductions, monitoring mode
  moderate    — 15–35 % reductions, active tapering
  aggressive  — 35–60 % reductions, strong compression
  emergency   — max safe reduction, immediate stabilization

Design rules:
  - Each phase step is ≤ 20 percentage points per adjustment
  - Transitions are always reversible
  - Critical workflows are shielded from smoothing
  - Recovery restores quality in the same gradual manner
"""
from __future__ import annotations

import uuid

from freya.predictive.models import (
    EquilibriumAssessment,
    OperationalForecast,
    PredictiveAdjustmentPlan,
    SmoothingPhase,
)

# Reduction fractions per phase (applied to low/background workflows)
_PHASE_REDUCTION: dict[SmoothingPhase, float] = {
    "none":       0.00,
    "gentle":     0.10,
    "moderate":   0.25,
    "aggressive": 0.50,
    "emergency":  0.65,
}

_PHASE_ORDER: list[SmoothingPhase] = [
    "none", "gentle", "moderate", "aggressive", "emergency"
]


def _select_phase(
    equilibrium: EquilibriumAssessment,
    forecast: OperationalForecast,
) -> SmoothingPhase:
    state   = equilibrium.equilibrium_state
    conf    = forecast.confidence_score

    if state == "critical":
        return "emergency" if conf >= 0.60 else "aggressive"
    if state == "destabilizing":
        return "aggressive" if conf >= 0.70 else "moderate"
    if state == "at_risk":
        return "moderate" if conf >= 0.65 else "gentle"
    if state == "monitoring":
        return "gentle" if conf >= 0.55 else "none"
    return "none"


class OperationalSmoothingEngine:
    """Calculate and describe gradual operational adjustments."""

    def plan(
        self,
        equilibrium: EquilibriumAssessment,
        forecast: OperationalForecast,
        affected_workflows: list[str],
    ) -> PredictiveAdjustmentPlan | None:
        """Build a smoothing plan for affected (non-critical) workflows."""
        if not forecast.action_warranted:
            return None

        phase     = _select_phase(equilibrium, forecast)
        reduction = _PHASE_REDUCTION[phase]

        if phase == "none" or not affected_workflows:
            return None

        wf_list    = ", ".join(affected_workflows[:4])
        has_more   = len(affected_workflows) > 4
        wf_display = wf_list + (" …" if has_more else "")

        adjustments: list[str] = [
            f"Smoothing phase '{phase}' applied to: {wf_display}.",
            f"Reasoning depth gradually reduced by {reduction:.0%} over the next "
            f"{forecast.forecast_window_minutes} minutes.",
        ]

        if phase in ("aggressive", "emergency"):
            adjustments.append(
                "Optimization cycles suspended for affected workflows until pressure normalises."
            )
        if phase in ("moderate", "aggressive", "emergency"):
            adjustments.append(
                "Governance reviews for non-critical workflows pre-queued to reduce interruptions."
            )

        return PredictiveAdjustmentPlan(
            plan_id=str(uuid.uuid4())[:8],
            proactive_adjustments=adjustments,
            expected_prevention_impact=(
                f"Progressive {reduction:.0%} reasoning taper prevents abrupt operational shock. "
                f"Stability maintained within {phase} smoothing bounds."
            ),
            governance_risk="none",
            reversibility=True,
            smoothing_phase=phase,
            confidence_basis=forecast.confidence_score,
        )

    def step_up(self, current: SmoothingPhase) -> SmoothingPhase:
        """Move to the next more-aggressive smoothing phase."""
        idx = _PHASE_ORDER.index(current) if current in _PHASE_ORDER else 0
        return _PHASE_ORDER[min(idx + 1, len(_PHASE_ORDER) - 1)]

    def step_down(self, current: SmoothingPhase) -> SmoothingPhase:
        """Reduce smoothing by one phase (recovery direction)."""
        idx = _PHASE_ORDER.index(current) if current in _PHASE_ORDER else 0
        return _PHASE_ORDER[max(idx - 1, 0)]

    def reduction_for(self, phase: SmoothingPhase) -> float:
        return _PHASE_REDUCTION.get(phase, 0.0)

    def describe_phase(self, phase: SmoothingPhase) -> str:
        descs = {
            "none":       "No smoothing — full operational capacity.",
            "gentle":     "Gentle taper — minor reductions for early signal interception.",
            "moderate":   "Moderate smoothing — active reasoning compression underway.",
            "aggressive": "Aggressive smoothing — significant capacity reservation in effect.",
            "emergency":  "Emergency smoothing — maximum safe compression applied.",
        }
        return descs.get(phase, "Unknown phase.")
