"""freya/strategic_governance/elasticity.py

Resilience Elasticity Cognition Engine.

Forecasts organizational elasticity thresholds and detects approaching
breaking points before collapse occurs. All forecasts are bounded,
operationally grounded, and deterministic — no speculative ML inference.
"""
from __future__ import annotations

from freya.strategic_governance.models import (
    ProjectedFailureRisk,
    ResilienceElasticityAssessment,
)


# ---------------------------------------------------------------------------
# Elasticity domain profiles
# Each entry: domain → (elasticity_threshold, preventive_action template)
# ---------------------------------------------------------------------------

_DOMAIN_PROFILES: dict[str, dict] = {
    "governance_review": {
        "threshold": 0.75,
        "description": "Governance review queue load relative to review board capacity.",
        "collapse_effect": "Review responsiveness degrades; critical decisions queue behind routine ones.",
        "preventive_action": (
            "Redistribute low-priority reviews to async channels. "
            "Reserve escalation slots for Severity-1 decisions. "
            "Activate temporary review delegation before queue reaches 80% capacity."
        ),
    },
    "analytical_trust": {
        "threshold": 0.70,
        "description": "Compression usage relative to analytical trust tolerance.",
        "collapse_effect": "Output confidence falls below organizational acceptance threshold.",
        "preventive_action": (
            "Reduce compression frequency by at least 30% this cycle. "
            "Rotate to batching or reservation to preserve trust headroom. "
            "Restore compression only after 2 trust-recovery cycles."
        ),
    },
    "recovery_responsiveness": {
        "threshold": 0.80,
        "description": "Active stabilization load relative to recovery path capacity.",
        "collapse_effect": "Recovery paths become saturated; response latency exceeds acceptable SLA.",
        "preventive_action": (
            "Pre-position alternate recovery path before primary becomes saturated. "
            "Reduce concurrent stabilization campaigns. "
            "Activate recovery sequencing throttling at 75% load."
        ),
    },
    "escalation_queue": {
        "threshold": 0.72,
        "description": "Escalation decision queue depth relative to resolution throughput.",
        "collapse_effect": "Escalation backlog accelerates; governance review latency compounds.",
        "preventive_action": (
            "Implement escalation triage: defer non-critical escalations 1 cycle. "
            "Activate governance batching for low-severity escalations. "
            "Reserve board capacity for incident-class decisions."
        ),
    },
    "adaptation_portfolio": {
        "threshold": 0.65,
        "description": "Monoculture risk in adaptation strategy usage.",
        "collapse_effect": "Single-strategy dependence creates systemic brittleness.",
        "preventive_action": (
            "Introduce at least two alternate stabilization strategies before primary "
            "strategy is unavailable. Rotate portfolios proactively — not reactively."
        ),
    },
    "operational_transparency": {
        "threshold": 0.68,
        "description": "Smoothing and masking load relative to transparency tolerance.",
        "collapse_effect": "Accountability opacity compounds; audit defensibility degrades.",
        "preventive_action": (
            "Reduce smoothing frequency. Transition to explicit quantitative interventions. "
            "Restore transparency metrics reporting before next audit window."
        ),
    },
}

_FAILURE_RISK_BANDS: list[tuple[float, ProjectedFailureRisk]] = [
    (0.50, "low"),
    (0.70, "moderate"),
    (0.85, "high"),
    (1.01, "critical"),
]


def _failure_risk(load: float, threshold: float) -> ProjectedFailureRisk:
    ratio = load / threshold if threshold > 0 else 1.0
    for cutoff, risk in _FAILURE_RISK_BANDS:
        if ratio < cutoff:
            return risk
    return "critical"


class ResilienceElasticityCognitionEngine:
    """Forecasts elasticity thresholds across organizational resilience domains."""

    def assess(
        self,
        domain: str,
        current_load: float,
        confidence: float = 0.70,
    ) -> ResilienceElasticityAssessment:
        """Return an elasticity assessment for a single domain.

        Parameters
        ----------
        domain:
            The organizational domain to assess (e.g. "governance_review").
        current_load:
            Normalized load metric [0.0, 1.0] — fraction of domain capacity consumed.
        confidence:
            Analytical confidence — low confidence lowers the effective threshold by 5%.
        """
        profile = _DOMAIN_PROFILES.get(domain)
        if profile is None:
            # Unknown domain — treat conservatively
            threshold = 0.70
            preventive = "Unknown domain. Treat as high-risk and monitor closely."
        else:
            threshold = profile["threshold"]
            preventive = profile["preventive_action"]
            if confidence < 0.55:
                threshold = max(0.50, threshold - 0.05)
                preventive = (
                    f"[LOW CONFIDENCE — conservative threshold applied] {preventive}"
                )

        risk = _failure_risk(current_load, threshold)

        return ResilienceElasticityAssessment(
            elasticity_domain=domain,
            current_load=round(current_load, 3),
            elasticity_threshold=round(threshold, 3),
            projected_failure_risk=risk,
            preventive_action=preventive,
        )

    def assess_all(
        self,
        domain_loads: dict[str, float],
        confidence: float = 0.70,
    ) -> list[ResilienceElasticityAssessment]:
        """Assess all provided domain loads."""
        return [
            self.assess(domain, load, confidence)
            for domain, load in domain_loads.items()
        ]

    def approaching_threshold(
        self, assessment: ResilienceElasticityAssessment
    ) -> bool:
        """Return True if load is within 15% of the elasticity threshold."""
        return assessment.current_load >= assessment.elasticity_threshold * 0.85

    def critical_domains(
        self, assessments: list[ResilienceElasticityAssessment]
    ) -> list[ResilienceElasticityAssessment]:
        """Return all assessments at high or critical failure risk."""
        return [a for a in assessments if a.projected_failure_risk in ("high", "critical")]

    def known_domains(self) -> list[str]:
        return list(_DOMAIN_PROFILES.keys())
