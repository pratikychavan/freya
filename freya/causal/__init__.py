"""freya/causal/__init__.py

Public API for the Causal Operational Reasoning Layer.

Example::

    from freya.causal import CausalReasoningPipeline

    result = CausalReasoningPipeline().run(
        active_event_types=["governance_congestion", "retry_spike"],
        interventions_applied=["batching_applied"],
        pressure=0.75,
        confidence=0.80,
    )
    print(result["render"])
"""
from __future__ import annotations

from freya.causal.chains import OperationalCausalChainEngine
from freya.causal.engine import CausalOperationalReasoningEngine, CausalReasoningReport
from freya.causal.governance import CausalGovernanceEngine
from freya.causal.interventions import CausalInterventionAnalysisEngine
from freya.causal.models import (
    CausalInterventionImpact,
    CausalPropagationChain,
    DestabilizationCascade,
    OperationalCausalEvent,
    StabilizationPropagation,
)
from freya.causal.propagation import OperationalPropagationEngine
from freya.causal.rendering import (
    render_cascade_analysis,
    render_causal_chain,
    render_intervention_causality,
    render_stabilization_propagation,
)
from freya.causal.stability import CausalStabilityEngine


class CausalReasoningPipeline:
    """Façade that orchestrates the full causal operational reasoning pipeline."""

    def __init__(self) -> None:
        self._engine = CausalOperationalReasoningEngine()

    def run(
        self,
        active_event_types: list[str],
        interventions_applied: list[str],
        pressure: float = 0.60,
        confidence: float = 0.70,
    ) -> dict:
        """Execute the full causal analysis and return a structured result.

        The returned dict includes:
        - ``report``           — :class:`CausalReasoningReport` (full structured output)
        - ``cascade_detected`` — bool
        - ``review_required``  — bool
        - ``render``           — human-readable multi-section string
        """
        report: CausalReasoningReport = self._engine.analyze(
            active_event_types=active_event_types,
            interventions_applied=interventions_applied,
            current_pressure=pressure,
            confidence=confidence,
        )

        render_sections: list[str] = []

        for chain in report.chains:
            render_sections.append(render_causal_chain(chain))

        if report.cascade is not None:
            render_sections.append(render_cascade_analysis(report.cascade))

        for impact in report.intervention_impacts:
            render_sections.append(render_intervention_causality(impact))

        for prop in report.stabilization_props:
            render_sections.append(render_stabilization_propagation(prop))

        if report.governance_violations:
            violation_block = (
                "┌─ Governance Observations ──────────────────────────────────────────┐\n"
                + "\n".join(f"│  ⚠  {v}" for v in report.governance_violations)
                + "\n└────────────────────────────────────────────────────────────────────┘"
            )
            render_sections.append(violation_block)

        return {
            "report": report,
            "cascade_detected": report.cascade_detected,
            "review_required": report.review_required,
            "render": "\n\n".join(render_sections),
        }


__all__ = [
    "CausalReasoningPipeline",
    "CausalOperationalReasoningEngine",
    "CausalReasoningReport",
    "OperationalCausalChainEngine",
    "OperationalPropagationEngine",
    "CausalStabilityEngine",
    "CausalInterventionAnalysisEngine",
    "CausalGovernanceEngine",
    "OperationalCausalEvent",
    "CausalPropagationChain",
    "CausalInterventionImpact",
    "DestabilizationCascade",
    "StabilizationPropagation",
    "render_causal_chain",
    "render_cascade_analysis",
    "render_intervention_causality",
    "render_stabilization_propagation",
]
