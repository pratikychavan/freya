"""freya/topology/governance.py

Topology Governance Engine.

Validates topology patterns, lifecycle states, and evolution assessments
against organizational governance rules. Governance always applies —
chronic isolation of critical workflows and recurring governance suppression
are hard-blocked here.
"""
from __future__ import annotations

from freya.topology.models import (
    OperationalTopologyPattern,
    TopologyEvolutionAssessment,
    TopologyLifecycleState,
)


class TopologyGovernanceEngine:
    """Validates topology cognition outputs against organizational governance rules."""

    # -----------------------------------------------------------------------
    # Pattern validation
    # -----------------------------------------------------------------------

    def validate_topology(
        self, pattern: OperationalTopologyPattern
    ) -> tuple[bool, list[str]]:
        """Validate an OperationalTopologyPattern against governance rules.

        Returns (is_valid, violations). A non-empty violations list always
        means is_valid=False.
        """
        violations: list[str] = []

        # Block chronic recurrence of governance suppression
        suppression_signals = {"governance_suppression", "governance_bypass", "governance_override"}
        pressure_patterns_lower = {p.lower() for p in pattern.recurring_pressure_patterns}
        if pattern.recurrence_frequency == "chronic" and pressure_patterns_lower & suppression_signals:
            violations.append(
                f"BLOCKED: '{pattern.topology_name}' has chronic recurrence of governance "
                "suppression patterns. Governance application is mandatory and cannot be "
                "systematically suppressed."
            )

        # Block chronic isolation of critical workflows
        critical_signals = {"critical_workflow_isolation", "critical_path_bypass", "critical_isolation"}
        partitions_lower = {p.lower() for p in pattern.recurring_partitions}
        if pattern.recurrence_frequency in ("frequent", "chronic") and partitions_lower & critical_signals:
            violations.append(
                f"BLOCKED: '{pattern.topology_name}' shows recurring isolation of critical "
                "workflows. Critical paths must remain accessible. Escalate to governance review."
            )

        # Warn if impact is severe but frequency is still low (early warning)
        if (
            pattern.recurrence_frequency in ("frequent", "chronic")
            and pattern.organizational_impact == "critical"
        ):
            violations.append(
                f"GOVERNANCE REVIEW REQUIRED: '{pattern.topology_name}' has {pattern.recurrence_frequency} "
                "recurrence with critical organizational impact. Executive review is mandatory before "
                "any topology adaptation decisions."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Lifecycle validation
    # -----------------------------------------------------------------------

    def validate_lifecycle(
        self, state: TopologyLifecycleState
    ) -> tuple[bool, list[str]]:
        """Validate a TopologyLifecycleState against governance rules."""
        violations: list[str] = []

        # Block: persistent stage + very low dissolution probability (chronic) without
        # active stabilization context (stabilization_maturity contains "Chronic" sentinel).
        is_chronic = (
            state.lifecycle_stage == "persistent"
            and state.dissolution_probability <= 0.15
        )
        not_stabilizing = "Chronic" in state.stabilization_maturity
        if is_chronic and not_stabilizing:
            violations.append(
                f"GOVERNANCE FLAG: '{state.topology_name}' is persistent with very low dissolution "
                f"probability ({state.dissolution_probability:.0%}) but insufficient stabilization "
                "maturity. This pattern may be entrenched without governance-approved stabilization — "
                "escalation required."
            )

        # Block: dissolving stage with high projected evolution risk
        if (
            state.lifecycle_stage == "dissolving"
            and state.projected_evolution_risk in ("high", "critical")
        ):
            violations.append(
                f"GOVERNANCE REVIEW: '{state.topology_name}' is dissolving with {state.projected_evolution_risk} "
                "projected evolution risk. Confirm dissolution intent before allowing topology to terminate."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Assessment validation
    # -----------------------------------------------------------------------

    def validate_assessment(
        self, assessment: TopologyEvolutionAssessment
    ) -> tuple[bool, list[str]]:
        """Validate a TopologyEvolutionAssessment against governance rules."""
        violations: list[str] = []

        # Block: chronic evolution state without a recommended adaptation
        if assessment.evolution_state == "chronic" and not assessment.recommended_adaptation.strip():
            violations.append(
                "BLOCKED: Chronic evolution state declared without a recommended adaptation. "
                "Governance requires an explicit adaptation plan before a chronic state is acted upon."
            )

        # Block: critical instability risk without sustainability degradation acknowledged
        if (
            assessment.chronic_instability_risk == "critical"
            and assessment.sustainability_outlook not in ("degrading", "critical")
        ):
            violations.append(
                "GOVERNANCE MISMATCH: Critical chronic instability risk does not align with "
                f"sustainability outlook '{assessment.sustainability_outlook}'. "
                "Review sustainability assessment before proceeding."
            )

        return (len(violations) == 0, violations)

    # -----------------------------------------------------------------------
    # Review gate
    # -----------------------------------------------------------------------

    def review_required(
        self,
        patterns: list[OperationalTopologyPattern],
        confidence: float,
    ) -> bool:
        """Return True when human governance review is required before acting.

        Triggers on:
        - confidence below 0.55
        - any chronic recurrence pattern present
        - any critical-impact pattern present
        """
        if confidence < 0.55:
            return True
        for p in patterns:
            if p.recurrence_frequency == "chronic":
                return True
            if p.organizational_impact == "critical":
                return True
        return False
