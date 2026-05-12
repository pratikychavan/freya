"""freya/resilience/engine.py

Organizational Resilience Cognition Engine.

Central coordinator: orchestrates reserve assessment, identity
preservation, portfolio balancing, continuity coordination, and
governance validation into a single bounded, explainable report.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from freya.resilience.continuity import OperationalContinuityCoordinationEngine
from freya.resilience.governance import ResilienceGovernanceEngine
from freya.resilience.identity import OrganizationalIdentityPreservationEngine
from freya.resilience.models import (
    AdaptationPortfolioState,
    ContinuityAssessment,
    OperationalResilienceReserve,
    OrganizationalIdentityProfile,
)
from freya.resilience.portfolio import AdaptationPortfolioBalancingEngine
from freya.resilience.reserves import OperationalResilienceReserveEngine


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

@dataclass
class ResilienceCognitionReport:
    """Complete output of one resilience cognition analysis cycle."""

    reserves: list[OperationalResilienceReserve]
    identity_profile: OrganizationalIdentityProfile
    portfolio_state: AdaptationPortfolioState
    continuity_assessment: ContinuityAssessment
    governance_violations: list[str] = field(default_factory=list)
    review_required: bool = False
    rotation_recommendation: str = ""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class OrganizationalResilienceCognitionEngine:
    """Orchestrates the full organizational resilience cognition pipeline."""

    def __init__(self) -> None:
        self._reserves = OperationalResilienceReserveEngine()
        self._identity = OrganizationalIdentityPreservationEngine()
        self._portfolio = AdaptationPortfolioBalancingEngine()
        self._continuity = OperationalContinuityCoordinationEngine()
        self._governance = ResilienceGovernanceEngine()

    def analyze(
        self,
        active_interventions: dict[str, int],
        confidence: float = 0.70,
    ) -> ResilienceCognitionReport:
        """Run a full resilience cognition analysis.

        Parameters
        ----------
        active_interventions:
            Mapping of intervention name → usage_cycles.
        confidence:
            Analytical confidence score [0.0, 1.0].
        """
        # Assess reserves
        reserves = self._reserves.assess_all(active_interventions, confidence)

        # Assess identity
        identity_profile = self._identity.assess(active_interventions)

        # Assess portfolio
        portfolio_state = self._portfolio.assess(
            active_strategies=list(active_interventions.keys()),
            usage_counts=active_interventions,
        )

        # Continuity assessment
        continuity = self._continuity.assess(
            reserves=reserves,
            identity_profile=identity_profile,
            portfolio_state=portfolio_state,
            confidence=confidence,
        )

        # Governance validation
        violations: list[str] = []
        for reserve in reserves:
            _, v = self._governance.validate_reserve(reserve)
            violations.extend(v)
        _, v = self._governance.validate_identity(identity_profile)
        violations.extend(v)
        _, v = self._governance.validate_portfolio(portfolio_state)
        violations.extend(v)
        _, v = self._governance.validate_continuity(continuity)
        violations.extend(v)

        # Review gate
        review_req = self._governance.review_required(reserves, confidence)

        # Rotation recommendation
        rotation_rec = self._portfolio.recommend_rotation(portfolio_state)

        return ResilienceCognitionReport(
            reserves=reserves,
            identity_profile=identity_profile,
            portfolio_state=portfolio_state,
            continuity_assessment=continuity,
            governance_violations=violations,
            review_required=review_req,
            rotation_recommendation=rotation_rec,
        )
