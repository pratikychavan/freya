"""freya/strategic_governance/__init__.py

Strategic Organizational Governance Cognition Layer — public façade.

Entry point: StrategicGovernancePipeline.run(...)
"""
from __future__ import annotations

from freya.strategic_governance.elasticity import ResilienceElasticityCognitionEngine
from freya.strategic_governance.engine import (
    StrategicGovernanceReport,
    StrategicOrganizationalGovernanceEngine,
)
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
from freya.strategic_governance.rendering import (
    render_elasticity_assessment,
    render_governance_sustainability,
    render_strategic_forecast,
    render_strategic_priorities,
)
from freya.strategic_governance.sustainability import GovernanceSustainabilityCognitionEngine


class StrategicGovernancePipeline:
    """High-level façade for the Strategic Organizational Governance Cognition Layer."""

    def __init__(self) -> None:
        self._engine = StrategicOrganizationalGovernanceEngine()

    def run(
        self,
        context: OperationalContext,
        domain_loads: dict[str, float] | None = None,
        review_load: float = 0.40,
        escalation_load: float = 0.35,
        horizon_cycles: int = 4,
        confidence: float = 0.70,
    ) -> dict:
        """Execute a full strategic governance cognition pipeline.

        Returns
        -------
        dict with keys:
            "report"          — StrategicGovernanceReport
            "review_required" — bool
            "context"         — str
            "render"          — str (formatted executive render)
        """
        report = self._engine.analyze(
            context=context,
            domain_loads=domain_loads,
            review_load=review_load,
            escalation_load=escalation_load,
            horizon_cycles=horizon_cycles,
            confidence=confidence,
        )

        render_sections: list[str] = []
        render_sections.append(render_strategic_priorities(report.priority_profile))

        for assessment in report.elasticity_assessments:
            render_sections.append(render_elasticity_assessment(assessment))

        render_sections.append(render_governance_sustainability(report.sustainability_state))
        render_sections.append(render_strategic_forecast(report.continuity_forecast))

        if report.governance_violations:
            violation_block = "GOVERNANCE VIOLATIONS DETECTED:\n" + "\n".join(
                f"  - {v}" for v in report.governance_violations
            )
            render_sections.append(violation_block)

        return {
            "report": report,
            "review_required": report.review_required,
            "context": report.context,
            "render": "\n\n".join(render_sections),
        }


__all__ = [
    "StrategicGovernancePipeline",
    "StrategicOrganizationalGovernanceEngine",
    "StrategicGovernanceReport",
    "StrategicPriorityCoordinationEngine",
    "ResilienceElasticityCognitionEngine",
    "GovernanceSustainabilityCognitionEngine",
    "StrategicContinuityForecastingEngine",
    "StrategicGovernanceOversightEngine",
    "StrategicGovernancePriority",
    "ResilienceElasticityAssessment",
    "GovernanceSustainabilityState",
    "StrategicContinuityForecast",
    "render_strategic_priorities",
    "render_elasticity_assessment",
    "render_governance_sustainability",
    "render_strategic_forecast",
]
