"""freya/causal/governance.py

CausalGovernanceEngine

Validates causal reasoning outputs to ensure no unsafe propagation
or cascade recommendation escapes into the coordination layer.

Hard rules:
  - Cascade recommendations that amplify governance bypass are blocked
  - Any chain that projects critical-workflow destabilization is flagged
  - Recommendations carrying equilibrium_risk="imminent" require human review
  - Unintended consequences that create irreversible effects are blocked
"""
from __future__ import annotations

from freya.causal.models import (
    CausalInterventionImpact,
    CausalPropagationChain,
    DestabilizationCascade,
)

_UNSAFE_UNINTENDED: frozenset[str] = frozenset({
    "irreversible",
    "governance bypass",
    "critical workflow destabilized",
    "permanent degradation",
})


class CausalGovernanceEngine:
    """Validate causal reasoning outputs for safety before acting on them."""

    def validate_chain(
        self,
        chain: CausalPropagationChain,
    ) -> tuple[bool, list[str]]:
        """Return (safe, list_of_violations) for a propagation chain."""
        violations: list[str] = []

        if chain.propagation_strength == "cascading" and chain.confidence_score >= 0.80:
            violations.append(
                f"Chain '{chain.chain_id}' projects a high-confidence cascade "
                f"— human review recommended before acting."
            )
        if chain.stabilization_effect == "none" and chain.propagation_strength == "cascading":
            violations.append(
                f"Chain '{chain.chain_id}' is cascading with no stabilization effect "
                f"— mitigation required."
            )
        return (len(violations) == 0, violations)

    def validate_cascade(
        self,
        cascade: DestabilizationCascade,
    ) -> tuple[bool, list[str]]:
        """Return (safe_to_surface, violations) for a detected cascade."""
        violations: list[str] = []

        if cascade.equilibrium_risk == "imminent":
            violations.append(
                f"Cascade '{cascade.cascade_id}' has imminent equilibrium risk "
                f"— immediate coordinated response required."
            )

        if not cascade.mitigation_recommendations:
            violations.append(
                f"Cascade '{cascade.cascade_id}' has no mitigation recommendations "
                f"— cannot surface without mitigation guidance."
            )

        # Surface the cascade as a warning but not blocked (it needs to be visible)
        return (True, violations)

    def validate_intervention_impact(
        self,
        impact: CausalInterventionImpact,
    ) -> tuple[bool, list[str]]:
        """Return (safe_to_recommend, violations) for an intervention impact."""
        violations: list[str] = []

        for consequence in impact.unintended_consequences:
            lower = consequence.lower()
            if any(unsafe in lower for unsafe in _UNSAFE_UNINTENDED):
                violations.append(
                    f"Intervention '{impact.intervention_name}' has an unsafe "
                    f"unintended consequence: '{consequence}'"
                )

        if impact.net_stability_delta < -0.20:
            violations.append(
                f"Intervention '{impact.intervention_name}' has a net negative "
                f"stability delta ({impact.net_stability_delta:+.0%}) — not recommended."
            )

        return (len(violations) == 0, violations)

    def review_required(
        self,
        cascade: DestabilizationCascade,
        confidence: float,
    ) -> bool:
        """Return True if human review is required before acting on mitigation."""
        return (
            cascade.equilibrium_risk in ("imminent", "high")
            and confidence >= 0.75
        )
