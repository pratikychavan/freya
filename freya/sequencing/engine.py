"""freya/sequencing/engine.py

Adaptive Coordination Sequencing Engine — central coordinator.

Orchestrates: phases → adaptation → recovery → equilibrium → governance.
All sequencing is bounded, explainable, and governance-approved.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from freya.sequencing.adaptation import AdaptiveInterventionEngine
from freya.sequencing.equilibrium import EquilibriumTransitionEngine
from freya.sequencing.governance import SequencingGovernanceEngine
from freya.sequencing.models import (
    AdaptiveInterventionDecision,
    CoordinationPhase,
    InterventionSequence,
    RecoveryProgression,
)
from freya.sequencing.phases import OperationalPhaseManagementEngine
from freya.sequencing.recovery import OperationalRecoveryCoordinationEngine

# ---------------------------------------------------------------------------
# Sequence templates
# ---------------------------------------------------------------------------
_SEQUENCE_TEMPLATES: dict[str, dict] = {
    "standard_stabilization": {
        "phases": [
            "Retry Stabilization",
            "Governance Recovery",
            "Contention Reduction",
            "Operational Restoration",
        ],
        "expected_stabilization_effect": (
            "Progressive reduction in retry churn, governance backlog, and contention; "
            "full restoration once pressure drops below 0.40."
        ),
        "projected_recovery_profile": (
            "Gradual — 4-phase progression; equilibrium maintained throughout."
        ),
        "confidence_score": 0.75,
    },
    "batching_led_recovery": {
        "phases": [
            "Governance Recovery",
            "Retry Stabilization",
            "Contention Reduction",
            "Operational Restoration",
        ],
        "expected_stabilization_effect": (
            "Governance queue relief reduces systemic retry amplification first; "
            "contention clears naturally as retry pressure falls."
        ),
        "projected_recovery_profile": (
            "Moderate — governance-first approach stabilizes retry pressure within 2 phases."
        ),
        "confidence_score": 0.73,
    },
    "conservative_recovery": {
        "phases": [
            "Retry Stabilization",
            "Contention Reduction",
            "Operational Restoration",
        ],
        "expected_stabilization_effect": (
            "Minimal-footprint stabilization; retry suppression clears contention naturally."
        ),
        "projected_recovery_profile": (
            "Slow but stable — suitable for low-confidence or fragile environments."
        ),
        "confidence_score": 0.60,
    },
    "emergency_stabilization": {
        "phases": [
            "Contention Reduction",
            "Retry Stabilization",
            "Governance Recovery",
            "Operational Restoration",
        ],
        "expected_stabilization_effect": (
            "Immediate pressure relief through contention suppression before addressing root causes."
        ),
        "projected_recovery_profile": (
            "Aggressive — contention-first; risk of rebound if recovery pacing is insufficient."
        ),
        "confidence_score": 0.65,
    },
}


@dataclass
class CoordinationSequencingReport:
    """Complete output from an adaptive coordination sequencing analysis."""

    active_event_types: list[str]
    active_interventions: list[str]
    current_pressure: float
    pressure_trend: str
    confidence: float

    recommended_sequence: InterventionSequence | None = None
    current_phase: CoordinationPhase | None = None
    adaptive_decision: AdaptiveInterventionDecision | None = None
    recovery_progression: RecoveryProgression | None = None
    equilibrium_assessment: dict = field(default_factory=dict)
    governance_violations: list[str] = field(default_factory=list)
    review_required: bool = False

    @property
    def is_safe_to_proceed(self) -> bool:
        return len(self.governance_violations) == 0

    @property
    def current_phase_name(self) -> str:
        if self.current_phase is None:
            return "unknown"
        return self.current_phase.phase_name


class AdaptiveCoordinationSequencingEngine:
    """Coordinates phased stabilization sequencing with adaptive, equilibrium-aware logic."""

    def __init__(self) -> None:
        self._phases = OperationalPhaseManagementEngine()
        self._adaptation = AdaptiveInterventionEngine()
        self._recovery = OperationalRecoveryCoordinationEngine()
        self._equilibrium = EquilibriumTransitionEngine()
        self._governance = SequencingGovernanceEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def sequence(
        self,
        active_event_types: list[str],
        active_interventions: list[str],
        current_pressure: float = 0.60,
        pressure_trend: str = "stable",
        confidence: float = 0.70,
    ) -> CoordinationSequencingReport:
        """Run a full adaptive coordination sequencing analysis.

        Args:
            active_event_types: Operational event types currently active.
            active_interventions: Interventions currently in effect.
            current_pressure: System pressure in [0.0, 1.0].
            pressure_trend: One of 'improving', 'stable', 'worsening'.
            confidence: Causal/operational confidence level in [0.0, 1.0].

        Returns:
            CoordinationSequencingReport with all sub-analyses populated.
        """
        report = CoordinationSequencingReport(
            active_event_types=list(active_event_types),
            active_interventions=list(active_interventions),
            current_pressure=current_pressure,
            pressure_trend=pressure_trend,
            confidence=confidence,
        )

        # 1. Select recommended sequence.
        sequence = self._select_sequence(
            active_event_types, current_pressure, pressure_trend, confidence
        )
        report.recommended_sequence = sequence

        # 2. Validate sequence through governance.
        valid, seq_violations = self._governance.validate_sequence(sequence)
        report.governance_violations.extend(seq_violations)

        # 3. Determine current phase.
        phase_name = self._phases.recommended_phase(
            active_event_types, current_pressure, pressure_trend
        )
        report.current_phase = self._phases.get_phase(phase_name)

        # 4. Adaptive intervention decision.
        decision = self._adaptation.recommend(
            current_phase=phase_name,
            current_pressure=current_pressure,
            active_interventions=active_interventions,
            pressure_trend=pressure_trend,
        )
        report.adaptive_decision = decision

        # Validate decision.
        _, dec_violations = self._governance.validate_decision(decision)
        report.governance_violations.extend(dec_violations)

        # 5. Recovery progression.
        recovery = self._recovery.assess_recovery(
            current_pressure=current_pressure,
            active_interventions=active_interventions,
            pressure_trend=pressure_trend,
        )
        report.recovery_progression = recovery

        # Validate recovery.
        _, rec_violations = self._governance.validate_recovery(recovery)
        report.governance_violations.extend(rec_violations)

        # 6. Equilibrium transition assessment (next phase).
        next_phases = self._phases.safe_next_phases(phase_name)
        if next_phases:
            next_phase = next_phases[0]
            report.equilibrium_assessment = self._equilibrium.assess_transition(
                from_phase=phase_name,
                to_phase=next_phase,
                current_pressure=current_pressure,
                recent_pressure_delta=0.0,  # caller may inject; default 0
            )
            # Validate transition.
            _, trans_violations = self._governance.validate_transition(
                phase_name, next_phase, current_pressure
            )
            report.governance_violations.extend(trans_violations)

        # 7. Human review requirement.
        report.review_required = self._governance.review_required(sequence, confidence)

        return report

    # ------------------------------------------------------------------
    # Sequence selection
    # ------------------------------------------------------------------
    def _select_sequence(
        self,
        active_event_types: list[str],
        pressure: float,
        trend: str,
        confidence: float,
    ) -> InterventionSequence:
        key = self._choose_sequence_key(active_event_types, pressure, trend, confidence)
        template = _SEQUENCE_TEMPLATES[key]
        return InterventionSequence(
            sequence_name=key,
            phases=template["phases"],
            expected_stabilization_effect=template["expected_stabilization_effect"],
            projected_recovery_profile=template["projected_recovery_profile"],
            confidence_score=template["confidence_score"],
        )

    def _choose_sequence_key(
        self,
        active_event_types: list[str],
        pressure: float,
        trend: str,
        confidence: float,
    ) -> str:
        if pressure > 0.70 or (len(active_event_types) >= 2 and trend == "worsening"):
            return "emergency_stabilization"
        if confidence < 0.55:
            return "conservative_recovery"
        if "governance_congestion" in active_event_types:
            return "batching_led_recovery"
        if "retry_spike" in active_event_types or "degradation_onset" in active_event_types:
            return "standard_stabilization"
        return "standard_stabilization"
