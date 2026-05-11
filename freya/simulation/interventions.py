"""freya/simulation/interventions.py

OperationalInterventionModelingEngine

Models the operational, governance, and coordination effects of each
intervention type. All effects are bounded and explainable.

Effect table (deterministic, telemetry-calibrated):
  governance_batching       — reduces approval interrupts; slight latency cost
  reasoning_compression     — reduces quality; fast stabilization
  workflow_degradation      — moderate quality loss; clear capacity gain
  reservation_reallocation  — protects critical workflows; may constrain others
  optimization_suspension   — eliminates opt overhead; defers quality gains
  workflow_deferral         — suspends low-pri tasks; moderate continuity impact
  no_intervention           — baseline; no change
"""
from __future__ import annotations

from freya.simulation.models import (
    InterventionEffect,
    InterventionType,
    OperationalScenario,
    SimulationOutcome,
)

# ── Effect table ───────────────────────────────────────────────────────────────

_EFFECT_TABLE: dict[InterventionType, InterventionEffect] = {
    "governance_batching": InterventionEffect(
        intervention_type="governance_batching",
        approval_interrupt_delta=-0.45,
        reasoning_quality_delta=-0.02,
        latency_delta_minutes=+2.5,
        stability_improvement=0.35,
        reversibility=True,
        recovery_difficulty="immediate",
        side_effects=["slight approval latency increase for low-priority tasks"],
    ),
    "reasoning_compression": InterventionEffect(
        intervention_type="reasoning_compression",
        approval_interrupt_delta=0.0,
        reasoning_quality_delta=-0.30,
        latency_delta_minutes=-1.5,
        stability_improvement=0.50,
        reversibility=True,
        recovery_difficulty="easy",
        side_effects=["shallower analysis for background workflows", "multi-step reasoning replaced by heuristics"],
    ),
    "workflow_degradation": InterventionEffect(
        intervention_type="workflow_degradation",
        approval_interrupt_delta=0.0,
        reasoning_quality_delta=-0.25,
        latency_delta_minutes=-2.0,
        stability_improvement=0.45,
        reversibility=True,
        recovery_difficulty="moderate",
        side_effects=["reduced workflow quality", "potential user-visible latency improvement"],
    ),
    "reservation_reallocation": InterventionEffect(
        intervention_type="reservation_reallocation",
        approval_interrupt_delta=0.0,
        reasoning_quality_delta=+0.10,   # improves for protected workflows
        latency_delta_minutes=-3.0,      # critical workflows faster
        stability_improvement=0.40,
        reversibility=True,
        recovery_difficulty="easy",
        side_effects=["lower-priority workflows may see capacity reduction"],
    ),
    "optimization_suspension": InterventionEffect(
        intervention_type="optimization_suspension",
        approval_interrupt_delta=0.0,
        reasoning_quality_delta=-0.10,
        latency_delta_minutes=-0.5,
        stability_improvement=0.25,
        reversibility=True,
        recovery_difficulty="easy",
        side_effects=["deferred optimization passes; quality gains delayed"],
    ),
    "workflow_deferral": InterventionEffect(
        intervention_type="workflow_deferral",
        approval_interrupt_delta=-0.15,
        reasoning_quality_delta=-0.05,
        latency_delta_minutes=0.0,
        stability_improvement=0.30,
        reversibility=True,
        recovery_difficulty="moderate",
        side_effects=["suspended workflows resume in next cycle"],
    ),
    "no_intervention": InterventionEffect(
        intervention_type="no_intervention",
        approval_interrupt_delta=0.0,
        reasoning_quality_delta=0.0,
        latency_delta_minutes=0.0,
        stability_improvement=0.0,
        reversibility=True,
        recovery_difficulty="immediate",
        side_effects=["no preventive action taken; risk remains"],
    ),
}


def _impact_label(quality_delta: float) -> str:
    if quality_delta <= -0.25:   return "significant"
    if quality_delta <= -0.15:   return "moderate"
    if quality_delta <= -0.05:   return "low"
    if quality_delta >= 0.05:    return "minimal"   # positive = improvement
    return "minimal"


def _governance_label(interrupt_delta: float) -> str:
    if interrupt_delta <= -0.30:  return "positive"
    if interrupt_delta <= -0.05:  return "neutral"
    if interrupt_delta == 0.0:    return "neutral"
    if interrupt_delta <= 0.10:   return "negative"
    return "critical"


def _recovery_minutes(effect: InterventionEffect, pressure: float) -> str:
    base = {"immediate": 0, "easy": 5, "moderate": 15, "complex": 40, "irreversible": 999}
    mins = base.get(effect.recovery_difficulty, 10) + int(pressure * 20)
    if mins == 0:   return "immediate"
    if mins >= 999: return "irreversible — not recommended"
    return f"~{mins} minutes"


class OperationalInterventionModelingEngine:
    """Model operational and governance effects of intervention types."""

    def model(
        self,
        scenario: OperationalScenario,
        current_pressure: float = 0.60,
        confidence: float = 0.70,
    ) -> SimulationOutcome:
        """Produce a SimulationOutcome for the given scenario."""
        effect   = _EFFECT_TABLE.get(scenario.intervention_type, _EFFECT_TABLE["no_intervention"])
        impact   = _impact_label(effect.reasoning_quality_delta)
        gov_eff  = _governance_label(effect.approval_interrupt_delta)
        recovery = _recovery_minutes(effect, current_pressure)

        stability_desc = (
            f"Stability improvement estimated at {effect.stability_improvement:.0%} "
            f"over {scenario.simulation_window_minutes} min window."
        )

        tradeoffs = list(effect.side_effects)
        if not effect.reversibility:
            tradeoffs.append("WARNING: This intervention is not fully reversible.")

        return SimulationOutcome(
            scenario_id=scenario.scenario_id,
            predicted_operational_impact=impact,  # type: ignore[arg-type]
            projected_governance_effect=gov_eff,   # type: ignore[arg-type]
            projected_recovery_time=recovery,
            projected_stability_effect=stability_desc,
            confidence_score=round(confidence * (0.8 + effect.stability_improvement * 0.2), 2),
            reversibility=effect.reversibility,
            recovery_difficulty=effect.recovery_difficulty,
            key_tradeoffs=tradeoffs,
        )

    def effect_for(self, intervention_type: InterventionType) -> InterventionEffect:
        return _EFFECT_TABLE.get(intervention_type, _EFFECT_TABLE["no_intervention"])

    def all_intervention_types(self) -> list[InterventionType]:
        return list(_EFFECT_TABLE.keys())
