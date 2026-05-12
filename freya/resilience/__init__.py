"""freya/resilience/__init__.py

Organizational Resilience & Identity Cognition Layer — public façade.

Entry point: OrganizationalResiliencePipeline.run(...)
"""
from __future__ import annotations

from freya.resilience.continuity import OperationalContinuityCoordinationEngine
from freya.resilience.engine import OrganizationalResilienceCognitionEngine, ResilienceCognitionReport
from freya.resilience.governance import ResilienceGovernanceEngine
from freya.resilience.identity import OrganizationalIdentityPreservationEngine
from freya.resilience.models import (
    AdaptationPortfolioState,
    ContinuityAssessment,
    OperationalResilienceReserve,
    OrganizationalIdentityProfile,
)
from freya.resilience.portfolio import AdaptationPortfolioBalancingEngine
from freya.resilience.rendering import (
    render_adaptation_portfolio,
    render_continuity_summary,
    render_identity_assessment,
    render_resilience_reserve,
)
from freya.resilience.reserves import OperationalResilienceReserveEngine


class OrganizationalResiliencePipeline:
    """High-level façade for the Organizational Resilience & Identity Cognition Layer."""

    def __init__(self) -> None:
        self._engine = OrganizationalResilienceCognitionEngine()

    def run(
        self,
        active_interventions: dict[str, int],
        confidence: float = 0.70,
    ) -> dict:
        """Execute a full resilience cognition pipeline.

        Parameters
        ----------
        active_interventions:
            Mapping of intervention name → usage_cycles.
        confidence:
            Analytical confidence score [0.0, 1.0].

        Returns
        -------
        dict with keys:
            "report"           — ResilienceCognitionReport
            "review_required"  — bool
            "continuity_state" — str
            "render"           — str (formatted executive render)
        """
        report = self._engine.analyze(
            active_interventions=active_interventions,
            confidence=confidence,
        )

        render_sections: list[str] = []

        for reserve in report.reserves:
            render_sections.append(render_resilience_reserve(reserve))

        render_sections.append(render_identity_assessment(report.identity_profile))
        render_sections.append(render_adaptation_portfolio(report.portfolio_state))
        render_sections.append(render_continuity_summary(report.continuity_assessment))

        if report.rotation_recommendation:
            render_sections.append(
                f"ADAPTATION ROTATION RECOMMENDATION:\n  {report.rotation_recommendation}"
            )

        if report.governance_violations:
            violation_block = "GOVERNANCE VIOLATIONS DETECTED:\n" + "\n".join(
                f"  - {v}" for v in report.governance_violations
            )
            render_sections.append(violation_block)

        return {
            "report": report,
            "review_required": report.review_required,
            "continuity_state": report.continuity_assessment.continuity_state,
            "render": "\n\n".join(render_sections),
        }


__all__ = [
    "OrganizationalResiliencePipeline",
    "OrganizationalResilienceCognitionEngine",
    "ResilienceCognitionReport",
    "OperationalResilienceReserveEngine",
    "OrganizationalIdentityPreservationEngine",
    "AdaptationPortfolioBalancingEngine",
    "OperationalContinuityCoordinationEngine",
    "ResilienceGovernanceEngine",
    "OperationalResilienceReserve",
    "OrganizationalIdentityProfile",
    "AdaptationPortfolioState",
    "ContinuityAssessment",
    "render_resilience_reserve",
    "render_identity_assessment",
    "render_adaptation_portfolio",
    "render_continuity_summary",
]
