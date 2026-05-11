"""freya/simulation/__init__.py

Operational Scenario Simulation Layer — public façade.

Quick start::

    from freya.simulation import OperationalSimulationPipeline
    from freya.simulation.models import OperationalScenario

    pipeline = OperationalSimulationPipeline()
    result = pipeline.run(
        scenarios=[
            OperationalScenario(
                scenario_id="s1",
                scenario_name="Governance Batching",
                intervention_type="governance_batching",
                intervention_description="Batch low-priority approvals.",
                affected_workflows=["wf-travel", "wf-reporting"],
                simulation_window_minutes=15,
            ),
        ],
        current_pressure=0.72,
        confidence=0.75,
    )
    print(result["report"])
"""
from __future__ import annotations

from freya.simulation.comparison import OperationalStrategyComparisonEngine, RankedStrategy
from freya.simulation.counterfactuals import CounterfactualOperationalReasoningEngine
from freya.simulation.engine import OperationalScenarioSimulationEngine, SimulationReport
from freya.simulation.forecasting import SimulationForecastingEngine
from freya.simulation.governance import SimulationGovernanceEngine
from freya.simulation.interventions import OperationalInterventionModelingEngine
from freya.simulation.models import (
    CounterfactualComparison,
    GovernanceEffect,
    InterventionEffect,
    InterventionType,
    OperationalImpact,
    OperationalScenario,
    RecoveryDifficulty,
    RiskLevel,
    SimulationOutcome,
    SimulationRiskAssessment,
)
from freya.simulation.rendering import (
    render_counterfactual_comparison,
    render_risk_assessment,
    render_simulation_outcome,
    render_simulation_scenario,
    render_strategy_recommendation,
)


class OperationalSimulationPipeline:
    """High-level façade for the operational scenario simulation layer."""

    def __init__(self) -> None:
        self._engine = OperationalScenarioSimulationEngine()

    def run(
        self,
        scenarios: list[OperationalScenario],
        current_pressure: float = 0.60,
        confidence: float = 0.70,
        has_critical_workflows: bool = False,
        baseline_scenario_id: str | None = None,
    ) -> dict:
        """Run a full simulation and return a structured result dict.

        Keys:
          - ``report``:      SimulationReport
          - ``render``:      human-readable string
          - ``recommended``: RankedStrategy | None
          - ``blocked``:     list[str] of blocked scenario IDs
        """
        report = self._engine.simulate(
            scenarios=scenarios,
            current_pressure=current_pressure,
            confidence=confidence,
            has_critical_workflows=has_critical_workflows,
            baseline_scenario_id=baseline_scenario_id,
        )
        render = self._build_render(report)
        return {
            "report":      report,
            "render":      render,
            "recommended": report.recommendation,
            "blocked":     report.blocked_scenarios,
        }

    def simulate_single(
        self,
        scenario: OperationalScenario,
        current_pressure: float = 0.60,
        confidence: float = 0.70,
        has_critical_workflows: bool = False,
    ) -> tuple[SimulationOutcome, SimulationRiskAssessment]:
        return self._engine.simulate_single(
            scenario, current_pressure, confidence, has_critical_workflows
        )

    # ── Private ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_render(report: SimulationReport) -> str:
        sections = [
            "═" * 70,
            "  OPERATIONAL SCENARIO SIMULATION — CYCLE REPORT",
            "═" * 70,
            "",
        ]

        # Scenario outcomes
        for scenario in report.scenarios:
            sections.append(render_simulation_scenario(scenario))
            outcome = report.outcomes.get(scenario.scenario_id)
            if outcome:
                sections.append(render_simulation_outcome(scenario, outcome))
            risk = report.risk_assessments.get(scenario.scenario_id)
            if risk:
                sections.append(render_risk_assessment(risk))
            sections.append("")

        # Strategy comparison table
        if report.ranked_strategies:
            comparison_table = OperationalStrategyComparisonEngine().comparison_table(
                report.ranked_strategies
            )
            recommended_name = (
                report.recommendation.scenario.scenario_name
                if report.recommendation else "None"
            )
            rec_reason = ""
            if report.counterfactual:
                rec_reason = report.counterfactual.recommendation_reason
            sections.append(
                render_strategy_recommendation(comparison_table, recommended_name, rec_reason)
            )

        # Counterfactual comparison
        if report.counterfactual:
            sections.append("")
            sections.append(render_counterfactual_comparison(report.counterfactual))

        # Advisory note
        if report.confidence_advisory:
            sections.append(
                "\n  [Advisory] Confidence below threshold — results are indicative only."
            )

        # Blocked scenarios
        if report.blocked_scenarios:
            sections.append(f"\n  Blocked scenarios: {', '.join(report.blocked_scenarios)}")

        sections.append("═" * 70)
        return "\n".join(sections)


__all__ = [
    # Pipeline
    "OperationalSimulationPipeline",
    # Engine + report
    "OperationalScenarioSimulationEngine",
    "SimulationReport",
    "RankedStrategy",
    # Sub-engines
    "OperationalInterventionModelingEngine",
    "SimulationForecastingEngine",
    "OperationalStrategyComparisonEngine",
    "CounterfactualOperationalReasoningEngine",
    "SimulationGovernanceEngine",
    # Models
    "OperationalScenario",
    "SimulationOutcome",
    "CounterfactualComparison",
    "SimulationRiskAssessment",
    "InterventionEffect",
    # Literals
    "InterventionType",
    "OperationalImpact",
    "GovernanceEffect",
    "RecoveryDifficulty",
    "RiskLevel",
    # Renderers
    "render_simulation_scenario",
    "render_simulation_outcome",
    "render_counterfactual_comparison",
    "render_strategy_recommendation",
    "render_risk_assessment",
]
