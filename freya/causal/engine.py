"""freya/causal/engine.py

Central coordinator for the Causal Operational Reasoning Layer.

All reasoning is bounded to operational telemetry.
No speculative causal world models. No governance bypass.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from freya.causal.chains import OperationalCausalChainEngine
from freya.causal.governance import CausalGovernanceEngine
from freya.causal.interventions import CausalInterventionAnalysisEngine
from freya.causal.models import (
    CausalInterventionImpact,
    CausalPropagationChain,
    DestabilizationCascade,
    StabilizationPropagation,
)
from freya.causal.propagation import OperationalPropagationEngine
from freya.causal.stability import CausalStabilityEngine


@dataclass
class CausalReasoningReport:
    """Complete output from a causal operational reasoning analysis."""

    active_event_types: list[str]
    interventions_applied: list[str]
    current_pressure: float
    confidence: float

    chains: list[CausalPropagationChain] = field(default_factory=list)
    propagation_spreads: list[dict] = field(default_factory=list)
    cascade: DestabilizationCascade | None = None
    intervention_impacts: list[CausalInterventionImpact] = field(default_factory=list)
    stabilization_props: list[StabilizationPropagation] = field(default_factory=list)
    governance_violations: list[str] = field(default_factory=list)
    review_required: bool = False

    @property
    def cascade_detected(self) -> bool:
        return self.cascade is not None

    @property
    def overall_stability_delta(self) -> float:
        if not self.intervention_impacts:
            return 0.0
        return sum(i.net_stability_delta for i in self.intervention_impacts) / len(
            self.intervention_impacts
        )

    @property
    def is_stabilizing(self) -> bool:
        return self.overall_stability_delta > 0.0


class CausalOperationalReasoningEngine:
    """Coordinates causal chain analysis, propagation, stability, interventions, and governance."""

    def __init__(self) -> None:
        self._chains = OperationalCausalChainEngine()
        self._propagation = OperationalPropagationEngine()
        self._stability = CausalStabilityEngine()
        self._interventions = CausalInterventionAnalysisEngine()
        self._governance = CausalGovernanceEngine()

    def analyze(
        self,
        active_event_types: list[str],
        interventions_applied: list[str],
        current_pressure: float = 0.60,
        confidence: float = 0.70,
    ) -> CausalReasoningReport:
        """Run a full causal operational reasoning analysis.

        Args:
            active_event_types: Operational event types currently active
                                 (e.g. ["governance_congestion", "retry_spike"]).
            interventions_applied: Interventions in effect
                                   (e.g. ["batching_applied", "smoothing_applied"]).
            current_pressure: System pressure as a float in [0.0, 1.0].
            confidence: Causal confidence level; applied uniformly unless
                        overridden per chain.

        Returns:
            CausalReasoningReport with all sub-analyses populated.
        """
        report = CausalReasoningReport(
            active_event_types=list(active_event_types),
            interventions_applied=list(interventions_applied),
            current_pressure=current_pressure,
            confidence=confidence,
        )

        # 1. Build chains for all active event types.
        for event_type in active_event_types:
            chain = self._chains.build(event_type, confidence_override=confidence)
            report.chains.append(chain)

            # 2. Estimate propagation spread per chain.
            spread = self._propagation.estimate_spread(
                chain=chain,
                active_event_types=active_event_types,
                current_pressure=current_pressure,
            )
            report.propagation_spreads.append(spread)

            # 3. Governance — validate chain.
            valid, violations = self._governance.validate_chain(chain)
            report.governance_violations.extend(violations)

        # 4. Detect destabilization cascade.
        report.cascade = self._propagation.detect_cascade(
            active_event_types=active_event_types,
            current_pressure=current_pressure,
            affected_workflow_count=max(1, len(active_event_types) * 3),
        )
        if report.cascade is not None:
            _, cascade_violations = self._governance.validate_cascade(report.cascade)
            report.governance_violations.extend(cascade_violations)
            report.review_required = self._governance.review_required(
                report.cascade, confidence
            )

        # 5. Analyse interventions.
        for intervention in interventions_applied:
            impact = self._interventions.analyze(intervention)
            report.intervention_impacts.append(impact)

            _, imp_violations = self._governance.validate_intervention_impact(impact)
            report.governance_violations.extend(imp_violations)

        # 6. Stabilization propagation per intervention.
        for intervention in interventions_applied:
            prop = self._stability.analyze(
                intervention_name=intervention,
                current_pressure=current_pressure,
            )
            report.stabilization_props.append(prop)

        return report
