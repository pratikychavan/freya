"""freya/strategic_governance/governance.py

Strategic Governance Oversight Engine.

Validates strategic adaptation decisions against organizational governance
rules. Restricts unsafe contextual tradeoffs, preserves governance
guarantees, and prevents strategic continuity degradation.
"""
from __future__ import annotations

from freya.strategic_governance.models import (
    GovernanceSustainabilityState,
    ResilienceElasticityAssessment,
    StrategicContinuityForecast,
    StrategicGovernancePriority,
)


class StrategicGovernanceOversightEngine:
    """Validates strategic governance cognition outputs against organizational rules."""

    # -----------------------------------------------------------------------
    # Priority validation
    # -----------------------------------------------------------------------

    def validate_priority(
        self, priority: StrategicGovernancePriority
    ) -> tuple[bool, list[str]]:
        """Validate a strategic priority profile against governance rules."""
        violations: list[str] = []

        # Governance rigor cannot be deprioritized in audit contexts
        if (
            priority.context_name == "audit"
            and "governance_rigor" in priority.temporarily_deprioritized
        ):
            violations.append(
                "BLOCKED: Governance rigor cannot be deprioritized during audit windows. "
                "Governance rigor is legally and organizationally non-negotiable during audits."
            )

        # Transparency cannot be fully deprioritized in any context
        if "operational_transparency" in priority.temporarily_deprioritized:
            violations.append(
                "GOVERNANCE ALERT: Operational transparency is being deprioritized. "
                "Transparency must remain above minimum threshold in all operational contexts. "
                "Review this priority configuration before applying."
            )

        # Trust degradation pattern detection
        trust_degrade_signals = {
            "analytical_trustworthiness",
        }
        if trust_degrade_signals.issubset(set(priority.temporarily_deprioritized)):
            violations.append(
                "GOVERNANCE FLAG: Analytical trustworthiness is being deprioritized. "
                "Trust reduction must remain tactical and time-bounded (≤ 2 cycles). "
                "Explicit restoration plan is required."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Elasticity validation
    # -----------------------------------------------------------------------

    def validate_elasticity(
        self, assessment: ResilienceElasticityAssessment
    ) -> tuple[bool, list[str]]:
        """Validate an elasticity assessment against governance rules."""
        violations: list[str] = []

        if assessment.projected_failure_risk == "critical":
            violations.append(
                f"BLOCKED: '{assessment.elasticity_domain}' is at critical failure risk "
                f"(load={assessment.current_load:.0%} vs threshold={assessment.elasticity_threshold:.0%}). "
                "No further load increase is permitted. Preventive action is mandatory before "
                "any new decisions are executed in this domain."
            )

        if (
            assessment.projected_failure_risk == "high"
            and assessment.elasticity_domain == "governance_review"
        ):
            violations.append(
                "GOVERNANCE ESCALATION: Governance review elasticity is at high failure risk. "
                "Review board capacity must be expanded or review redistribution activated "
                "before the next governance decision cycle."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Sustainability validation
    # -----------------------------------------------------------------------

    def validate_sustainability(
        self, state: GovernanceSustainabilityState
    ) -> tuple[bool, list[str]]:
        """Validate a governance sustainability state against governance rules."""
        violations: list[str] = []

        if state.governance_capacity_state == "critical":
            violations.append(
                "BLOCKED: Governance process is at critical capacity. "
                "New governance-requiring decisions must be deferred until capacity is restored. "
                "Executive escalation is mandatory."
            )

        if state.sustainability_outlook == "unsustainable":
            violations.append(
                "GOVERNANCE ALERT: Governance sustainability is unsustainable. "
                "Review redistribution and capacity expansion are required this cycle. "
                "Governance continuity cannot be recovered reactively — act now."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Forecast validation
    # -----------------------------------------------------------------------

    def validate_forecast(
        self, forecast: StrategicContinuityForecast
    ) -> tuple[bool, list[str]]:
        """Validate a continuity forecast against governance rules."""
        violations: list[str] = []

        trust_risks = {r for r in forecast.anticipated_risks if "trust" in r.lower()}
        if trust_risks and "analytical_trustworthiness" not in forecast.protected_operational_characteristics:
            violations.append(
                "GOVERNANCE FLAG: Trust degradation risks are anticipated but analytical "
                "trustworthiness is not in the protected characteristics list. "
                "Ensure trust is explicitly protected in the continuity strategy."
            )

        if (
            "governance_rigor" not in forecast.protected_operational_characteristics
            and len(forecast.anticipated_risks) > 2
        ):
            violations.append(
                "GOVERNANCE REVIEW REQUIRED: Multiple continuity risks anticipated without "
                "governance rigor declared as a protected characteristic. "
                "Governance-aware continuity planning is required."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Review gate
    # -----------------------------------------------------------------------

    def review_required(
        self,
        assessments: list[ResilienceElasticityAssessment],
        sustainability: GovernanceSustainabilityState,
        confidence: float,
    ) -> bool:
        """Return True when human governance review is required before proceeding.

        Triggers on:
        - confidence < 0.55
        - any critical elasticity domain
        - saturated or critical governance capacity
        """
        if confidence < 0.55:
            return True
        for a in assessments:
            if a.projected_failure_risk in ("critical", "high"):
                return True
        if sustainability.governance_capacity_state in ("critical", "saturated"):
            return True
        return False
