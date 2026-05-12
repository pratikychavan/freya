"""freya/resilience/continuity.py

Operational Continuity Coordination Engine.

Synthesizes reserve depletion, identity drift, and portfolio balance
into a single continuity assessment. Preserves organizational
continuity characteristics — not merely infrastructure uptime.
"""
from __future__ import annotations

from freya.resilience.models import (
    AdaptationPortfolioState,
    ContinuityAssessment,
    ContinuityState,
    OperationalResilienceReserve,
    OperationalTrustLevel,
    OrganizationalIdentityProfile,
    ResilienceOutlook,
)


# Risk scoring weights
_DEPLETION_RISK_SCORE = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
_BALANCE_SCORE = {"balanced": 0, "skewed": 1, "monoculture": 2}
_PRIORITY_SCORE = {"standard": 0, "elevated": 1, "critical": 2}


def _continuity_state(total_risk: int) -> ContinuityState:
    if total_risk <= 1:
        return "stable"
    if total_risk <= 3:
        return "at_risk"
    if total_risk <= 6:
        return "degrading"
    return "critical"


def _trust_level(
    identity: OrganizationalIdentityProfile,
    reserves: list[OperationalResilienceReserve],
) -> OperationalTrustLevel:
    # Trust is mainly driven by identity drift signals
    signals = identity.degradation_signals
    if "deep_analytical_trust_degradation" in signals:
        return "degraded"
    if "analytical_trust_erosion" in signals or identity.preservation_priority == "critical":
        return "low"
    if identity.degradation_signals:
        return "moderate"
    # Check if compression reserve is heavily depleted
    for r in reserves:
        if r.reserve_type == "compression" and r.depletion_risk == "critical":
            return "low"
    return "high"


def _resilience_outlook(
    reserves: list[OperationalResilienceReserve],
    portfolio: AdaptationPortfolioState,
    confidence: float,
) -> ResilienceOutlook:
    critical_count = sum(1 for r in reserves if r.depletion_risk == "critical")
    high_count = sum(1 for r in reserves if r.depletion_risk == "high")
    if critical_count >= 2 or (critical_count >= 1 and portfolio.rotation_balance == "monoculture"):
        return "critical"
    if critical_count >= 1 or high_count >= 2 or confidence < 0.50:
        return "concerning"
    if high_count >= 1 or portfolio.rotation_balance == "skewed":
        return "watchlist"
    return "healthy"


def _future_recovery_capacity(
    reserves: list[OperationalResilienceReserve],
    confidence: float,
) -> str:
    critical = [r.reserve_type for r in reserves if r.depletion_risk == "critical"]
    high = [r.reserve_type for r in reserves if r.depletion_risk == "high"]
    if critical:
        names = ", ".join(critical)
        return (
            f"RESTRICTED: Critical depletion in [{names}] severely limits future stabilization "
            "flexibility. Replenishment must occur before next destabilization event."
        )
    if high:
        names = ", ".join(high)
        return (
            f"REDUCED: High depletion in [{names}] narrows future stabilization options. "
            "Replenish before high-severity events to preserve response range."
        )
    if confidence < 0.55:
        return (
            "UNCERTAIN: Low confidence limits recovery capacity projection. "
            "Initiate conservative pacing to preserve optionality."
        )
    return "HEALTHY: Sufficient stabilization reserves remain for future events."


def _strategic_risk(
    continuity_state: ContinuityState,
    outlook: ResilienceOutlook,
    portfolio: AdaptationPortfolioState,
) -> str:
    if continuity_state == "critical":
        return (
            "CRITICAL: Continuity degradation is systemic. Immediate governance escalation "
            "and portfolio reset are required before next stabilization cycle."
        )
    if continuity_state == "degrading" or outlook == "critical":
        return (
            "HIGH: Compounding reserve depletion and identity drift create systemic risk. "
            "Intervention rotation required this cycle."
        )
    if portfolio.rotation_balance == "monoculture":
        return (
            "ELEVATED: Adaptation monoculture increases brittleness risk. "
            "Diversify stabilization portfolio before pressure recurs."
        )
    if continuity_state == "at_risk":
        return (
            "MODERATE: Early resilience stress detected. Maintain conservative reserve "
            "usage and review portfolio balance at next cycle."
        )
    return "LOW: Organizational continuity is stable. Routine monitoring sufficient."


class OperationalContinuityCoordinationEngine:
    """Synthesizes reserves, identity, and portfolio into a continuity assessment."""

    def assess(
        self,
        reserves: list[OperationalResilienceReserve],
        identity_profile: OrganizationalIdentityProfile,
        portfolio_state: AdaptationPortfolioState,
        confidence: float = 0.70,
    ) -> ContinuityAssessment:
        """Return a ContinuityAssessment given current operational context.

        Parameters
        ----------
        reserves:
            List of assessed resilience reserves.
        identity_profile:
            Current organizational identity profile.
        portfolio_state:
            Current adaptation portfolio state.
        confidence:
            Analytical confidence [0.0, 1.0].
        """
        # Aggregate risk score
        reserve_risk = sum(
            _DEPLETION_RISK_SCORE[r.depletion_risk] for r in reserves
        )
        balance_risk = _BALANCE_SCORE[portfolio_state.rotation_balance]
        identity_risk = _PRIORITY_SCORE[identity_profile.preservation_priority]
        total_risk = reserve_risk + balance_risk + identity_risk

        state = _continuity_state(total_risk)
        trust = _trust_level(identity_profile, reserves)
        outlook = _resilience_outlook(reserves, portfolio_state, confidence)
        recovery = _future_recovery_capacity(reserves, confidence)
        risk = _strategic_risk(state, outlook, portfolio_state)

        return ContinuityAssessment(
            continuity_state=state,
            operational_trust_level=trust,
            resilience_outlook=outlook,
            future_recovery_capacity=recovery,
            strategic_risk=risk,
        )
