"""freya/simulation/engine.py

OperationalScenarioSimulationEngine

Central coordinator for the scenario simulation layer.
Accepts a set of intervention scenarios, models their effects,
validates governance safety, and returns ranked, comparable outcomes.

Design rules:
  - All simulation is bounded, deterministic, and telemetry-driven
  - Governance safety is validated before any recommendation
  - Critical-workflow degradation is always blocked
  - Low-confidence simulations produce advisory output only
"""
from __future__ import annotations

from dataclasses import dataclass, field

from freya.simulation.comparison import OperationalStrategyComparisonEngine, RankedStrategy
from freya.simulation.counterfactuals import CounterfactualOperationalReasoningEngine
from freya.simulation.forecasting import SimulationForecastingEngine
from freya.simulation.governance import SimulationGovernanceEngine
from freya.simulation.interventions import OperationalInterventionModelingEngine
from freya.simulation.models import (
    CounterfactualComparison,
    OperationalScenario,
    SimulationOutcome,
    SimulationRiskAssessment,
)


@dataclass
class SimulationReport:
    """Complete output from one simulation cycle."""
    scenarios:           list[OperationalScenario]
    outcomes:            dict[str, SimulationOutcome]
    risk_assessments:    dict[str, SimulationRiskAssessment]
    ranked_strategies:   list[RankedStrategy]
    recommendation:      RankedStrategy | None
    counterfactual:      CounterfactualComparison | None
    confidence_advisory: bool = False   # True when confidence is too low for firm recommendation
    blocked_scenarios:   list[str] = field(default_factory=list)


class OperationalScenarioSimulationEngine:
    """Orchestrates bounded operational scenario simulation."""

    def __init__(self) -> None:
        self._modeling       = OperationalInterventionModelingEngine()
        self._forecasting    = SimulationForecastingEngine()
        self._comparison     = OperationalStrategyComparisonEngine()
        self._counterfactual = CounterfactualOperationalReasoningEngine()
        self._governance     = SimulationGovernanceEngine()

    def simulate(
        self,
        scenarios: list[OperationalScenario],
        current_pressure: float = 0.60,
        confidence: float = 0.70,
        has_critical_workflows: bool = False,
        baseline_scenario_id: str | None = None,
    ) -> SimulationReport:
        """Run a full simulation cycle over the provided scenarios."""

        # 1. Model outcomes for every scenario
        outcomes: dict[str, SimulationOutcome] = {}
        for scenario in scenarios:
            outcomes[scenario.scenario_id] = self._modeling.model(
                scenario=scenario,
                current_pressure=current_pressure,
                confidence=confidence,
            )

        # 2. Governance validation — filter unsafe scenarios
        risk_assessments = self._governance.validate_batch(
            scenarios=scenarios,
            outcomes=outcomes,
            has_critical_workflows=has_critical_workflows,
        )
        blocked = [sid for sid, r in risk_assessments.items() if not r.safe_to_proceed]
        safe_scenarios = [s for s in scenarios if s.scenario_id not in blocked]

        # 3. Rank safe scenarios
        safe_outcomes = {sid: outcomes[sid] for sid in outcomes if sid not in blocked}
        ranked = self._comparison.rank(
            scenarios=safe_scenarios,
            outcomes=safe_outcomes,
            current_pressure=current_pressure,
        )

        # 4. Recommend (confidence-gated)
        confidence_advisory = confidence < 0.50
        threshold = 0.40 if confidence_advisory else 0.50
        recommendation = self._comparison.recommend(ranked, confidence_threshold=threshold)

        # 5. Counterfactual comparison
        counterfactual: CounterfactualComparison | None = None
        if baseline_scenario_id and len(safe_scenarios) >= 2:
            baseline = next(
                (s for s in safe_scenarios if s.scenario_id == baseline_scenario_id), None
            )
            alternatives = [s for s in safe_scenarios if s.scenario_id != baseline_scenario_id]
            if baseline and alternatives:
                try:
                    counterfactual = self._counterfactual.compare(
                        baseline_scenario=baseline,
                        alternative_scenarios=alternatives,
                        outcomes=safe_outcomes,
                        current_pressure=current_pressure,
                    )
                except ValueError:
                    pass

        return SimulationReport(
            scenarios=scenarios,
            outcomes=outcomes,
            risk_assessments=risk_assessments,
            ranked_strategies=ranked,
            recommendation=recommendation,
            counterfactual=counterfactual,
            confidence_advisory=confidence_advisory,
            blocked_scenarios=blocked,
        )

    def simulate_single(
        self,
        scenario: OperationalScenario,
        current_pressure: float = 0.60,
        confidence: float = 0.70,
        has_critical_workflows: bool = False,
    ) -> tuple[SimulationOutcome, SimulationRiskAssessment]:
        """Simulate and validate a single scenario."""
        outcome = self._modeling.model(scenario, current_pressure, confidence)
        risk    = self._governance.assess_risk(scenario, outcome, has_critical_workflows)
        return outcome, risk
