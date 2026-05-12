"""freya/sequencing/__init__.py

Public API for the Coordination Sequencing + Adaptive Intervention Layer.

Example::

    from freya.sequencing import CoordinationSequencingPipeline

    result = CoordinationSequencingPipeline().run(
        active_event_types=["governance_congestion", "retry_spike"],
        active_interventions=["batching_applied"],
        pressure=0.72,
        pressure_trend="stable",
        confidence=0.75,
    )
    print(result["render"])
"""
from __future__ import annotations

from freya.sequencing.adaptation import AdaptiveInterventionEngine
from freya.sequencing.engine import (
    AdaptiveCoordinationSequencingEngine,
    CoordinationSequencingReport,
)
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
from freya.sequencing.rendering import (
    render_adaptive_decision,
    render_coordination_sequence,
    render_phase_transition,
    render_recovery_progression,
)


class CoordinationSequencingPipeline:
    """Façade that orchestrates the full coordination sequencing pipeline."""

    def __init__(self) -> None:
        self._engine = AdaptiveCoordinationSequencingEngine()

    def run(
        self,
        active_event_types: list[str],
        active_interventions: list[str],
        pressure: float = 0.60,
        pressure_trend: str = "stable",
        confidence: float = 0.70,
    ) -> dict:
        """Execute the full sequencing analysis and return a structured result.

        The returned dict includes:
        - ``report``          — :class:`CoordinationSequencingReport`
        - ``review_required`` — bool
        - ``is_safe``         — bool (no governance violations)
        - ``render``          — human-readable multi-section string
        """
        report: CoordinationSequencingReport = self._engine.sequence(
            active_event_types=active_event_types,
            active_interventions=active_interventions,
            current_pressure=pressure,
            pressure_trend=pressure_trend,
            confidence=confidence,
        )

        render_sections: list[str] = []

        if report.recommended_sequence is not None:
            render_sections.append(render_coordination_sequence(report.recommended_sequence))

        if report.adaptive_decision is not None:
            render_sections.append(render_adaptive_decision(report.adaptive_decision))

        if report.recovery_progression is not None:
            render_sections.append(render_recovery_progression(report.recovery_progression))

        if report.equilibrium_assessment:
            from_phase = report.current_phase.phase_name if report.current_phase else "unknown"
            next_phases = OperationalPhaseManagementEngine().safe_next_phases(
                from_phase.lower().replace(" ", "_")
            )
            to_phase = next_phases[0] if next_phases else "unknown"
            render_sections.append(
                render_phase_transition(from_phase, to_phase, report.equilibrium_assessment)
            )

        if report.governance_violations:
            block = (
                "┌─ Governance Observations ──────────────────────────────────────────┐\n"
                + "\n".join(f"│  ⚠  {v}" for v in report.governance_violations)
                + "\n└────────────────────────────────────────────────────────────────────┘"
            )
            render_sections.append(block)

        return {
            "report": report,
            "review_required": report.review_required,
            "is_safe": report.is_safe_to_proceed,
            "render": "\n\n".join(render_sections),
        }


__all__ = [
    "CoordinationSequencingPipeline",
    "AdaptiveCoordinationSequencingEngine",
    "CoordinationSequencingReport",
    "OperationalPhaseManagementEngine",
    "AdaptiveInterventionEngine",
    "OperationalRecoveryCoordinationEngine",
    "EquilibriumTransitionEngine",
    "SequencingGovernanceEngine",
    "CoordinationPhase",
    "InterventionSequence",
    "AdaptiveInterventionDecision",
    "RecoveryProgression",
    "render_coordination_sequence",
    "render_phase_transition",
    "render_adaptive_decision",
    "render_recovery_progression",
]
