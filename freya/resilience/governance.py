"""freya/resilience/governance.py

Resilience Governance Engine.

Validates resilience adaptations against organizational governance rules.
Blocks identity-damaging stabilization, prevents resilience exhaustion,
and preserves governance guarantees at all times.
"""
from __future__ import annotations

from freya.resilience.models import (
    AdaptationPortfolioState,
    ContinuityAssessment,
    OperationalResilienceReserve,
    OrganizationalIdentityProfile,
)


class ResilienceGovernanceEngine:
    """Validates resilience outputs and enforces organizational governance rules."""

    # -----------------------------------------------------------------------
    # Reserve validation
    # -----------------------------------------------------------------------

    def validate_reserve(
        self, reserve: OperationalResilienceReserve
    ) -> tuple[bool, list[str]]:
        """Validate a resilience reserve against governance rules."""
        violations: list[str] = []

        if reserve.depletion_risk == "critical":
            violations.append(
                f"BLOCKED: Reserve '{reserve.reserve_type}' is at critical depletion "
                f"(capacity={reserve.current_capacity:.0%}). Further use requires "
                "governance approval. Activate replenishment strategy before proceeding."
            )

        if reserve.reserve_type == "compression" and reserve.depletion_risk in ("high", "critical"):
            violations.append(
                f"GOVERNANCE ALERT: Compression reserve is {reserve.depletion_risk} — "
                "analytical trust is at risk. Compression frequency must be reduced "
                "this cycle regardless of stabilization pressure."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Identity validation
    # -----------------------------------------------------------------------

    def validate_identity(
        self, profile: OrganizationalIdentityProfile
    ) -> tuple[bool, list[str]]:
        """Validate an identity profile against governance rules."""
        violations: list[str] = []

        if profile.preservation_priority == "critical":
            violations.append(
                "BLOCKED: Organizational identity is at critical degradation risk. "
                "Identity-damaging stabilization patterns must be stopped immediately. "
                "Governance escalation is mandatory before resuming aggressive interventions."
            )

        if "governance_rigor_fatigue" in profile.degradation_signals:
            violations.append(
                "GOVERNANCE RULE VIOLATION: Governance rigor fatigue detected. "
                "Governance review quality cannot be compromised — reduce review frequency "
                "and restore review board capacity before next decision cycle."
            )

        if "transparency_masking" in profile.degradation_signals:
            violations.append(
                "GOVERNANCE ALERT: Operational transparency is being masked by prolonged "
                "smoothing. Transparency is a core governance requirement — transition to "
                "explicit interventions immediately."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Portfolio validation
    # -----------------------------------------------------------------------

    def validate_portfolio(
        self, portfolio: AdaptationPortfolioState
    ) -> tuple[bool, list[str]]:
        """Validate an adaptation portfolio against governance rules."""
        violations: list[str] = []

        if portfolio.rotation_balance == "monoculture":
            dominant = (
                max(portfolio.active_strategies, key=lambda s: s)
                if portfolio.active_strategies else "unknown"
            )
            violations.append(
                f"GOVERNANCE FLAG: Adaptation portfolio is in monoculture mode "
                f"(sustainability_score={portfolio.sustainability_score:.0%}). "
                "Adaptation diversity is a resilience requirement — introduce at least "
                "one alternate strategy before the next stabilization cycle."
            )

        if portfolio.sustainability_score <= 0.30:
            violations.append(
                f"GOVERNANCE ALERT: Portfolio sustainability is critically low "
                f"({portfolio.sustainability_score:.0%}). "
                "Current adaptation regime is unsustainable — portfolio reset required."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Continuity validation
    # -----------------------------------------------------------------------

    def validate_continuity(
        self, assessment: ContinuityAssessment
    ) -> tuple[bool, list[str]]:
        """Validate a continuity assessment against governance rules."""
        violations: list[str] = []

        if assessment.continuity_state == "critical":
            violations.append(
                "BLOCKED: Organizational continuity is in critical state. "
                "No further stabilization adaptation is permitted without "
                "executive governance review and explicit approval."
            )

        if assessment.operational_trust_level == "degraded":
            violations.append(
                "GOVERNANCE ESCALATION: Operational trust has degraded below acceptable "
                "threshold. Trust restoration must be prioritized over all other "
                "stabilization objectives."
            )

        if assessment.resilience_outlook == "critical":
            violations.append(
                "GOVERNANCE REVIEW REQUIRED: Resilience outlook is critical. "
                "Reserve replenishment and portfolio diversification must occur "
                "this cycle — subsequent decisions require governance sign-off."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Review gate
    # -----------------------------------------------------------------------

    def review_required(
        self,
        reserves: list[OperationalResilienceReserve],
        confidence: float,
    ) -> bool:
        """Return True when human governance review is required before proceeding.

        Triggers on:
        - confidence < 0.55
        - any critical reserve depletion
        - more than one high-depletion reserve
        """
        if confidence < 0.55:
            return True
        critical_count = sum(1 for r in reserves if r.depletion_risk == "critical")
        high_count = sum(1 for r in reserves if r.depletion_risk == "high")
        return critical_count >= 1 or high_count >= 2
