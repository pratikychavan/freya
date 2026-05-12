"""freya/strategic_governance/engine.py

Strategic Organizational Governance Engine.

Central coordinator: orchestrates priority alignment, elasticity
forecasting, governance sustainability, and continuity forecasting
into a single bounded, explainable report.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from freya.strategic_governance.elasticity import ResilienceElasticityCognitionEngine
from freya.strategic_governance.forecasting import StrategicContinuityForecastingEngine
from freya.strategic_governance.governance import StrategicGovernanceOversightEngine
from freya.strategic_governance.models import (
    GovernanceSustainabilityState,
    OperationalContext,
    ResilienceElasticityAssessment,
    StrategicContinuityForecast,
    StrategicGovernancePriority,
)
from freya.strategic_governance.priorities import StrategicPriorityCoordinationEngine
from freya.strategic_governance.sustainability import GovernanceSustainabilityCognitionEngine


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

@dataclass
class StrategicGovernanceReport:
    """Complete output of one strategic governance cognition cycle."""

    context: str
    priority_profile: StrategicGovernancePriority
    elasticity_assessments: list[ResilienceElasticityAssessment]
    sustainability_state: GovernanceSustainabilityState
    continuity_forecast: StrategicContinuityForecast
    governance_violations: list[str] = field(default_factory=list)
    review_required: bool = False


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class StrategicOrganizationalGovernanceEngine:
    """Orchestrates the full strategic governance cognition pipeline."""

    def __init__(self) -> None:
        self._priorities = StrategicPriorityCoordinationEngine()
        self._elasticity = ResilienceElasticityCognitionEngine()
        self._sustainability = GovernanceSustainabilityCognitionEngine()
        self._forecasting = StrategicContinuityForecastingEngine()
        self._governance = StrategicGovernanceOversightEngine()

    def analyze(
        self,
        context: OperationalContext,
        domain_loads: dict[str, float] | None = None,
        review_load: float = 0.40,
        escalation_load: float = 0.35,
        horizon_cycles: int = 4,
        confidence: float = 0.70,
    ) -> StrategicGovernanceReport:
        """Run a full strategic governance cognition analysis.

        Parameters
        ----------
        context:
            Current operational regime.
        domain_loads:
            Mapping of elasticity domain → normalized load [0.0, 1.0].
        review_load:
            Governance review queue pressure [0.0, 1.0].
        escalation_load:
            Escalation queue saturation [0.0, 1.0].
        horizon_cycles:
            Forward-looking cycle horizon for continuity forecast.
        confidence:
            Analytical confidence score [0.0, 1.0].
        """
        # Strategic priority profile
        priority = self._priorities.prioritize(context, confidence)

        # Elasticity assessments
        assessments: list[ResilienceElasticityAssessment] = []
        if domain_loads:
            assessments = self._elasticity.assess_all(domain_loads, confidence)
        # Always include governance_review as a baseline elasticity check
        if "governance_review" not in (domain_loads or {}):
            assessments.append(
                self._elasticity.assess("governance_review", review_load, confidence)
            )

        # Governance sustainability
        sustainability = self._sustainability.assess(review_load, escalation_load, confidence)

        # Continuity forecast
        forecast = self._forecasting.forecast(context, horizon_cycles, confidence)

        # Governance validation
        violations: list[str] = []
        _, v = self._governance.validate_priority(priority)
        violations.extend(v)
        for assessment in assessments:
            _, v = self._governance.validate_elasticity(assessment)
            violations.extend(v)
        _, v = self._governance.validate_sustainability(sustainability)
        violations.extend(v)
        _, v = self._governance.validate_forecast(forecast)
        violations.extend(v)

        # Review gate
        review_req = self._governance.review_required(assessments, sustainability, confidence)

        return StrategicGovernanceReport(
            context=context,
            priority_profile=priority,
            elasticity_assessments=assessments,
            sustainability_state=sustainability,
            continuity_forecast=forecast,
            governance_violations=violations,
            review_required=review_req,
        )
