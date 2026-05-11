"""freya/simulation/comparison.py

OperationalStrategyComparisonEngine

Ranks multiple intervention strategies, compares organizational impact,
and recommends the least-disruptive option that achieves stability goals.

Optimization target: organizational continuity — not arbitrary metrics.
"""
from __future__ import annotations

from freya.simulation.models import (
    InterventionType,
    OperationalScenario,
    SimulationOutcome,
)
from freya.simulation.interventions import OperationalInterventionModelingEngine
from freya.simulation.forecasting import SimulationForecastingEngine

_modeling    = OperationalInterventionModelingEngine()
_forecasting = SimulationForecastingEngine()

# Scoring weights
_W_STABILITY   = 0.35
_W_GOVERNANCE  = 0.25
_W_REVERSIBLE  = 0.20
_W_IMPACT      = 0.20

_GOVERNANCE_SCORES: dict[str, float] = {
    "positive": 1.00,
    "neutral":  0.75,
    "none":     0.60,
    "negative": 0.25,
    "critical": 0.0,
}

_IMPACT_SCORES: dict[str, float] = {
    "minimal":     1.00,
    "low":         0.80,
    "moderate":    0.55,
    "significant": 0.30,
    "severe":      0.0,
}


class RankedStrategy:
    """A scored, ranked intervention strategy."""

    def __init__(
        self,
        scenario: OperationalScenario,
        outcome: SimulationOutcome,
        score: float,
        stabilization_probability: float,
        recovery_minutes: int,
    ) -> None:
        self.scenario                 = scenario
        self.outcome                  = outcome
        self.score                    = score
        self.stabilization_probability = stabilization_probability
        self.recovery_minutes         = recovery_minutes

    def summary(self) -> list[str]:
        return [
            f"Score:         {self.score:.2f} / 1.00",
            f"Stability prob:{self.stabilization_probability:.0%}",
            f"Recovery:      ~{self.recovery_minutes} min",
            f"Gov. effect:   {self.outcome.projected_governance_effect}",
            f"Impact:        {self.outcome.predicted_operational_impact}",
            f"Reversible:    {'Yes' if self.outcome.reversibility else 'No'}",
        ]


class OperationalStrategyComparisonEngine:
    """Rank and compare operational intervention strategies."""

    def rank(
        self,
        scenarios: list[OperationalScenario],
        outcomes: dict[str, SimulationOutcome],
        current_pressure: float = 0.60,
    ) -> list[RankedStrategy]:
        """Return scenarios ranked from most to least suitable."""
        ranked: list[RankedStrategy] = []

        for scenario in scenarios:
            outcome = outcomes.get(scenario.scenario_id)
            if outcome is None:
                continue
            effect  = _modeling.effect_for(scenario.intervention_type)
            score   = self._compute_score(outcome, effect)
            stab_p  = _forecasting.estimate_stabilization_probability(
                current_pressure, effect, scenario.simulation_window_minutes
            )
            rec_min = _forecasting.estimate_recovery_minutes(
                current_pressure, effect, scenario.simulation_window_minutes
            )
            ranked.append(RankedStrategy(scenario, outcome, score, stab_p, rec_min))

        ranked.sort(key=lambda r: r.score, reverse=True)
        return ranked

    def recommend(
        self,
        ranked: list[RankedStrategy],
        confidence_threshold: float = 0.50,
    ) -> RankedStrategy | None:
        """Return the top-ranked strategy meeting the confidence threshold."""
        for r in ranked:
            if r.outcome.confidence_score >= confidence_threshold:
                return r
        return ranked[0] if ranked else None

    def comparison_table(
        self,
        ranked: list[RankedStrategy],
    ) -> list[dict]:
        """Return a structured comparison table for rendering."""
        return [
            {
                "rank":         i + 1,
                "scenario":     r.scenario.scenario_name,
                "score":        round(r.score, 2),
                "impact":       r.outcome.predicted_operational_impact,
                "governance":   r.outcome.projected_governance_effect,
                "stability_p":  f"{r.stabilization_probability:.0%}",
                "recovery_min": r.recovery_minutes,
                "reversible":   r.outcome.reversibility,
            }
            for i, r in enumerate(ranked)
        ]

    # ── Private ────────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_score(outcome: SimulationOutcome, effect) -> float:
        stability_score = effect.stability_improvement
        gov_score       = _GOVERNANCE_SCORES.get(outcome.projected_governance_effect, 0.50)
        reversible_score = 1.0 if outcome.reversibility else 0.30
        impact_score    = _IMPACT_SCORES.get(outcome.predicted_operational_impact, 0.50)

        return (
            stability_score   * _W_STABILITY   +
            gov_score         * _W_GOVERNANCE  +
            reversible_score  * _W_REVERSIBLE  +
            impact_score      * _W_IMPACT
        )
