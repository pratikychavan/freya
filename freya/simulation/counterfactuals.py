"""freya/simulation/counterfactuals.py

CounterfactualOperationalReasoningEngine

Compares intervention alternatives against a baseline (typically no_intervention)
to reason about avoided disruption and relative operational outcomes.

"What if no batching occurs?"
"What if aggressive compression is applied instead?"
"What if reservations are delayed?"

All comparisons are bounded by operational telemetry and intervention effects.
No abstract speculation.
"""
from __future__ import annotations

from freya.simulation.models import (
    CounterfactualComparison,
    InterventionType,
    OperationalScenario,
    SimulationOutcome,
)
from freya.simulation.interventions import OperationalInterventionModelingEngine

_modeling = OperationalInterventionModelingEngine()


class CounterfactualOperationalReasoningEngine:
    """Compare multiple intervention scenarios against a baseline."""

    def compare(
        self,
        baseline_scenario: OperationalScenario,
        alternative_scenarios: list[OperationalScenario],
        outcomes: dict[str, SimulationOutcome],
        current_pressure: float = 0.60,
    ) -> CounterfactualComparison:
        """Produce a counterfactual comparison of scenarios against the baseline."""
        baseline_outcome = outcomes.get(baseline_scenario.scenario_id)
        if baseline_outcome is None:
            raise ValueError(f"Baseline outcome missing for {baseline_scenario.scenario_id}")

        # Rank alternatives by stability improvement vs baseline
        ranked = sorted(
            alternative_scenarios,
            key=lambda s: self._rank_score(s, outcomes, baseline_outcome, current_pressure),
            reverse=True,
        )

        best = ranked[0] if ranked else baseline_scenario
        best_outcome = outcomes.get(best.scenario_id, baseline_outcome)

        tradeoffs = self._describe_tradeoffs(
            baseline_scenario, baseline_outcome, best, best_outcome
        )

        return CounterfactualComparison(
            baseline_scenario=baseline_scenario.scenario_id,
            compared_scenarios=[s.scenario_id for s in alternative_scenarios],
            recommended_strategy=best.scenario_id,
            recommendation_reason=self._recommendation_reason(
                baseline_scenario, baseline_outcome, best, best_outcome
            ),
            organizational_tradeoffs=tradeoffs,
            confidence_score=best_outcome.confidence_score,
        )

    def avoided_disruption_description(
        self,
        baseline: SimulationOutcome,
        recommended: SimulationOutcome,
    ) -> list[str]:
        """Describe what disruption is avoided by choosing the recommended scenario."""
        lines = []
        if baseline.predicted_operational_impact in ("significant", "severe"):
            lines.append(
                f"Without intervention, operational impact would be "
                f"'{baseline.predicted_operational_impact}'. "
                f"Recommended scenario reduces this to '{recommended.predicted_operational_impact}'."
            )
        if baseline.projected_governance_effect in ("negative", "critical"):
            lines.append(
                f"Governance disruption avoided: effect improves from "
                f"'{baseline.projected_governance_effect}' to '{recommended.projected_governance_effect}'."
            )
        if not lines:
            lines.append(
                "Recommended strategy provides comparable or improved outcomes with lower coordination risk."
            )
        return lines

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _rank_score(
        scenario: OperationalScenario,
        outcomes: dict[str, SimulationOutcome],
        baseline_outcome: SimulationOutcome,
        pressure: float,
    ) -> float:
        outcome = outcomes.get(scenario.scenario_id)
        if outcome is None:
            return 0.0

        effect = _modeling.effect_for(scenario.intervention_type)

        # Higher stability improvement = better
        score = effect.stability_improvement * 0.40

        # Better governance effect = better
        gov_scores = {"positive": 0.30, "neutral": 0.20, "none": 0.15, "negative": 0.05, "critical": 0.0}
        score += gov_scores.get(outcome.projected_governance_effect, 0.10)

        # Reversibility bonus
        if outcome.reversibility:
            score += 0.15

        # Confidence bonus
        score += outcome.confidence_score * 0.15

        # Penalty for severe impact
        impact_penalties = {"minimal": 0, "low": 0.05, "moderate": 0.10, "significant": 0.20, "severe": 0.35}
        score -= impact_penalties.get(outcome.predicted_operational_impact, 0)

        return score

    @staticmethod
    def _recommendation_reason(
        baseline: OperationalScenario,
        baseline_out: SimulationOutcome,
        recommended: OperationalScenario,
        rec_out: SimulationOutcome,
    ) -> str:
        rec_effect = _modeling.effect_for(recommended.intervention_type)
        base_effect = _modeling.effect_for(baseline.intervention_type)

        improvement = rec_effect.stability_improvement - base_effect.stability_improvement

        if improvement > 0.10:
            return (
                f"'{recommended.scenario_name}' provides {improvement:.0%} greater stability improvement "
                f"than '{baseline.scenario_name}' with comparable governance risk."
            )
        if rec_out.projected_governance_effect in ("positive", "neutral") and \
           baseline_out.projected_governance_effect in ("negative", "critical"):
            return (
                f"'{recommended.scenario_name}' preserves governance continuity "
                f"where '{baseline.scenario_name}' would create disruption."
            )
        return (
            f"'{recommended.scenario_name}' achieves organizational stability "
            f"with lower coordination disruption and comparable recovery complexity."
        )

    @staticmethod
    def _describe_tradeoffs(
        baseline: OperationalScenario,
        baseline_out: SimulationOutcome,
        recommended: OperationalScenario,
        rec_out: SimulationOutcome,
    ) -> list[str]:
        tradeoffs = []

        rec_effect  = _modeling.effect_for(recommended.intervention_type)
        base_effect = _modeling.effect_for(baseline.intervention_type)

        if rec_effect.reasoning_quality_delta < base_effect.reasoning_quality_delta:
            tradeoffs.append(
                "Recommended strategy involves slightly greater reasoning quality reduction."
            )
        if rec_effect.latency_delta_minutes > base_effect.latency_delta_minutes:
            tradeoffs.append(
                "Recommended strategy has marginally higher approval latency."
            )
        if rec_out.recovery_difficulty != baseline_out.recovery_difficulty:
            tradeoffs.append(
                f"Recovery complexity: {recommended.scenario_name} ({rec_out.recovery_difficulty}) "
                f"vs {baseline.scenario_name} ({baseline_out.recovery_difficulty})."
            )
        if not tradeoffs:
            tradeoffs.append("No significant tradeoffs compared to baseline.")

        return tradeoffs
