"""freya/strategic_governance/priorities.py

Strategic Priority Coordination Engine.

Contextually shifts which organizational characteristics are prioritized
based on the current operational regime. All priority shifts are:
  - explainable via rationale strings
  - reversible (no permanent policy changes)
  - governed (core constraints are non-negotiable)
"""
from __future__ import annotations

from freya.strategic_governance.models import OperationalContext, StrategicGovernancePriority


# ---------------------------------------------------------------------------
# Context-specific priority templates
# ---------------------------------------------------------------------------

_PRIORITY_TEMPLATES: dict[str, dict] = {
    "normal": {
        "prioritized": ["governance_rigor", "analytical_trustworthiness", "operational_transparency"],
        "deprioritized": [],
        "constraints": [
            "Governance rigor must be maintained at standard threshold.",
            "All adaptation decisions require normal review process.",
        ],
        "rationale": (
            "Standard operational mode: balanced prioritization across all organizational "
            "characteristics. No characteristic is elevated or deprioritized."
        ),
    },
    "incident": {
        "prioritized": ["responsiveness", "recovery_quality", "governance_rigor"],
        "deprioritized": ["optimization_efficiency", "analytical_trustworthiness"],
        "constraints": [
            "Governance rigor must remain non-negotiable — incident response is not a governance bypass.",
            "Analytical trust reduction is tactical only; restore within 2 cycles of incident resolution.",
        ],
        "rationale": (
            "Incident escalation window: responsiveness and recovery speed temporarily outweigh "
            "optimization efficiency, but governance rigor remains mandatory."
        ),
    },
    "audit": {
        "prioritized": ["governance_rigor", "operational_transparency", "analytical_trustworthiness"],
        "deprioritized": ["responsiveness", "optimization_efficiency"],
        "constraints": [
            "Governance rigor cannot be compromised for any reason during audit windows.",
            "Transparency is legally required — smoothing is prohibited during audit scope.",
        ],
        "rationale": (
            "Audit window: governance rigor and operational transparency are the primary "
            "organizational characteristics. Speed and optimization are deprioritized to "
            "ensure audit defensibility."
        ),
    },
    "release_window": {
        "prioritized": ["recovery_quality", "responsiveness", "operational_transparency"],
        "deprioritized": ["governance_rigor"],
        "constraints": [
            "Governance rigor can be temporarily streamlined but not eliminated — "
            "minimum review thresholds still apply.",
            "Recovery quality must be actively preserved during release transition.",
        ],
        "rationale": (
            "Release transition window: continuity and recovery elasticity are prioritized "
            "to absorb release-related operational variance. Governance is streamlined, "
            "not suspended."
        ),
    },
    "migration": {
        "prioritized": ["recovery_quality", "governance_rigor", "responsiveness"],
        "deprioritized": ["optimization_efficiency", "analytical_trustworthiness"],
        "constraints": [
            "Migration decisions require explicit governance sign-off before execution.",
            "Recovery quality cannot be compromised — rollback capacity must be preserved.",
        ],
        "rationale": (
            "Migration window: recovery flexibility and governance oversight are critical. "
            "Optimization and analytical depth are temporarily secondary to migration success."
        ),
    },
    "governance_review": {
        "prioritized": ["governance_rigor", "analytical_trustworthiness", "operational_transparency"],
        "deprioritized": ["responsiveness", "optimization_efficiency"],
        "constraints": [
            "All adaptation decisions during governance review must pass heightened scrutiny.",
            "Trust and transparency are primary — no compression or smoothing permitted.",
        ],
        "rationale": (
            "Governance review period: rigor, trust, and transparency dominate. "
            "Adaptation aggressiveness is reduced to support clean audit trail."
        ),
    },
}


class StrategicPriorityCoordinationEngine:
    """Produces contextual governance priority profiles."""

    def prioritize(
        self,
        context: OperationalContext,
        confidence: float = 0.70,
    ) -> StrategicGovernancePriority:
        """Return a StrategicGovernancePriority for the given operational context.

        Parameters
        ----------
        context:
            Current operational regime identifier.
        confidence:
            Analytical confidence — low confidence adds an advisory constraint.
        """
        template = _PRIORITY_TEMPLATES.get(context, _PRIORITY_TEMPLATES["normal"])

        constraints = list(template["constraints"])
        if confidence < 0.55:
            constraints.append(
                "LOW CONFIDENCE: Priority shift is advisory only. "
                "Do not act on deprioritization without governance confirmation."
            )

        return StrategicGovernancePriority(
            context_name=context,
            prioritized_characteristics=template["prioritized"],
            temporarily_deprioritized=template["deprioritized"],
            governance_constraints=constraints,
            rationale=template["rationale"],
        )

    def supported_contexts(self) -> list[str]:
        return list(_PRIORITY_TEMPLATES.keys())
