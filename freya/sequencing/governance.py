"""freya/sequencing/governance.py

Sequencing Governance Layer.

Validates intervention ordering, phase transitions, and adaptive decisions
to ensure all sequencing remains bounded, explainable, and auditable.

Hard rules:
- Restoration phase may not begin while pressure > 0.50
- Phases may not be skipped without an explicit justification flag
- Unsafe recovery actions are blocked outright
- High-confidence emergency escalations require human review
"""
from __future__ import annotations

from freya.sequencing.models import (
    AdaptiveInterventionDecision,
    InterventionSequence,
    RecoveryProgression,
)

# ---------------------------------------------------------------------------
# Governance constants
# ---------------------------------------------------------------------------
_MAX_RESTORATION_PRESSURE = 0.50

_UNSAFE_ACTIONS: frozenset[str] = frozenset(
    {
        "immediate full restoration",
        "skip stabilization",
        "bypass governance",
        "force optimization",
        "aggressive compression",
        "instant recovery",
        "full restoration",
    }
)

_PROHIBITED_PHASE_SKIPS: dict[str, list[str]] = {
    # Phases that MUST precede restoration in any standard sequence.
    "restoration": ["contention_reduction"],
}

_REVIEW_REQUIRED_SEQUENCES = frozenset(
    {"emergency_stabilization"}
)


class SequencingGovernanceEngine:
    """Validates sequencing artifacts before they are actioned."""

    # ------------------------------------------------------------------
    # Sequence validation
    # ------------------------------------------------------------------
    def validate_sequence(
        self, sequence: InterventionSequence
    ) -> tuple[bool, list[str]]:
        """Validate an InterventionSequence for governance compliance.

        Returns (is_valid, violations).
        """
        violations: list[str] = []

        # Restoration must not appear before contention_reduction in any sequence.
        phases = sequence.phases
        for phase, prerequisites in _PROHIBITED_PHASE_SKIPS.items():
            if phase in phases:
                phase_idx = phases.index(phase)
                for prereq in prerequisites:
                    if prereq not in phases[:phase_idx]:
                        violations.append(
                            f"Sequence '{sequence.sequence_name}': "
                            f"'{phase}' present without required prerequisite '{prereq}'."
                        )

        if sequence.confidence_score < 0.40:
            violations.append(
                f"Sequence '{sequence.sequence_name}' confidence {sequence.confidence_score:.0%} "
                "is too low for operational commitment — conservative monitoring recommended."
            )

        return (len(violations) == 0, violations)

    # ------------------------------------------------------------------
    # Phase transition validation
    # ------------------------------------------------------------------
    def validate_transition(
        self,
        from_phase: str,
        to_phase: str,
        current_pressure: float,
    ) -> tuple[bool, list[str]]:
        """Validate a proposed phase transition.

        Returns (is_valid, violations).
        """
        violations: list[str] = []

        if to_phase == "restoration" and current_pressure > _MAX_RESTORATION_PRESSURE:
            violations.append(
                f"Transition to 'restoration' blocked: pressure {current_pressure:.0%} "
                f"exceeds maximum {_MAX_RESTORATION_PRESSURE:.0%}. "
                "Pressure must reduce before restoration can begin."
            )

        return (len(violations) == 0, violations)

    # ------------------------------------------------------------------
    # Adaptive decision validation
    # ------------------------------------------------------------------
    def validate_decision(
        self, decision: AdaptiveInterventionDecision
    ) -> tuple[bool, list[str]]:
        """Validate an adaptive intervention decision.

        Returns (is_valid, violations).
        """
        violations: list[str] = []
        action_lower = decision.recommended_next_action.lower()

        for unsafe in _UNSAFE_ACTIONS:
            if unsafe in action_lower:
                violations.append(
                    f"Decision blocked: recommended action contains unsafe pattern '{unsafe}'. "
                    "Gradual bounded restoration is required."
                )

        return (len(violations) == 0, violations)

    # ------------------------------------------------------------------
    # Recovery progression validation
    # ------------------------------------------------------------------
    def validate_recovery(
        self, progression: RecoveryProgression
    ) -> tuple[bool, list[str]]:
        """Validate a recovery progression for safe pacing.

        Returns (is_valid, violations).
        """
        violations: list[str] = []

        for action in progression.restoration_actions:
            action_lower = action.lower()
            for unsafe in _UNSAFE_ACTIONS:
                if unsafe in action_lower:
                    violations.append(
                        f"Recovery action '{action[:60]}...' "
                        f"contains unsafe pattern '{unsafe}'."
                    )

        if (
            progression.recovery_stage in ("restoring", "complete")
            and progression.stabilization_confidence < 0.70
        ):
            violations.append(
                f"Recovery stage '{progression.recovery_stage}' requires confidence ≥ 0.70; "
                f"current confidence is {progression.stabilization_confidence:.0%}."
            )

        return (len(violations) == 0, violations)

    # ------------------------------------------------------------------
    # Human review requirement
    # ------------------------------------------------------------------
    def review_required(
        self,
        sequence: InterventionSequence,
        confidence: float,
    ) -> bool:
        """Return True when the sequence warrants human review before execution."""
        if sequence.sequence_name in _REVIEW_REQUIRED_SEQUENCES:
            return True
        if confidence < 0.55:
            return True
        if sequence.confidence_score < 0.50:
            return True
        return False
