"""freya/topology/engine.py

Organizational Topology Evolution Engine.

Central coordinator for the topology evolution layer. Orchestrates
lifecycle management, memory retrieval, evolution analysis, sustainability
assessment, and governance validation into a single coherent report.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from freya.topology.evolution import TopologyEvolutionAnalysisEngine
from freya.topology.governance import TopologyGovernanceEngine
from freya.topology.lifecycle import TopologyLifecycleManagementEngine
from freya.topology.memory import OperationalTopologyMemoryEngine
from freya.topology.models import (
    OperationalMemoryRecord,
    OperationalTopologyPattern,
    TopologyEvolutionAssessment,
    TopologyLifecycleState,
)
from freya.topology.sustainability import LongHorizonOperationalSustainabilityEngine


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

@dataclass
class TopologyEvolutionReport:
    """Complete output of one topology evolution analysis cycle."""

    patterns: list[OperationalTopologyPattern]
    lifecycle_states: dict[str, TopologyLifecycleState]
    memory_records: list[OperationalMemoryRecord]
    assessment: TopologyEvolutionAssessment | None
    sustainability: dict
    governance_violations: list[str]
    review_required: bool


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

# Recurrence frequency mapping from occurrence count
def _recurrence_frequency(count: int) -> str:
    if count <= 1:
        return "rare"
    if count <= 3:
        return "occasional"
    if count <= 7:
        return "frequent"
    return "chronic"


class OrganizationalTopologyEvolutionEngine:
    """Orchestrates the full organizational topology evolution analysis pipeline."""

    def __init__(self) -> None:
        self._lifecycle = TopologyLifecycleManagementEngine()
        self._memory = OperationalTopologyMemoryEngine()
        self._evolution = TopologyEvolutionAnalysisEngine()
        self._sustainability = LongHorizonOperationalSustainabilityEngine()
        self._governance = TopologyGovernanceEngine()

    def analyze(
        self,
        topology_occurrences: dict[str, int],
        active_interventions: list[str] | None = None,
        confidence: float = 0.70,
        horizon_cycles: int = 5,
    ) -> TopologyEvolutionReport:
        """Run a full topology evolution analysis.

        Parameters
        ----------
        topology_occurrences:
            Mapping of topology name → number of observed occurrences.
        active_interventions:
            Currently active operational interventions (for sustainability analysis).
        confidence:
            Analytical confidence score [0.0, 1.0].
        horizon_cycles:
            Forward-looking cycle horizon for sustainability assessment.
        """
        active_interventions = active_interventions or []

        # Build topology patterns from occurrence data
        patterns: list[OperationalTopologyPattern] = []
        for name, count in topology_occurrences.items():
            freq = _recurrence_frequency(count)
            patterns.append(
                OperationalTopologyPattern(
                    topology_name=name,
                    recurring_partitions=[],
                    recurring_pressure_patterns=[],
                    recurrence_frequency=freq,
                    organizational_impact=(
                        "critical" if freq == "chronic"
                        else "significant" if freq == "frequent"
                        else "moderate"
                    ),
                )
            )

        # Assess lifecycle state for each pattern
        lifecycle_states: dict[str, TopologyLifecycleState] = {}
        for name, count in topology_occurrences.items():
            lifecycle_states[name] = self._lifecycle.assess_lifecycle(name, count)

        # Retrieve relevant memory signals
        active_signals = {p.recurrence_frequency for p in patterns}
        memory_records = self._memory.recall_all_for_context(
            active_signals, active_interventions
        )

        # Analyze evolution
        assessment: TopologyEvolutionAssessment | None = None
        governance_violations: list[str] = []

        if patterns:
            assessment = self._evolution.analyze(patterns, confidence)

            # Validate assessment
            asses_valid, asses_violations = self._governance.validate_assessment(assessment)
            governance_violations.extend(asses_violations)

        # Validate patterns
        for pattern in patterns:
            valid, violations = self._governance.validate_topology(pattern)
            governance_violations.extend(violations)

        # Validate lifecycle states
        for state in lifecycle_states.values():
            valid, violations = self._governance.validate_lifecycle(state)
            governance_violations.extend(violations)

        # Sustainability assessment
        sustainability = self._sustainability.assess(
            active_topology_count=len(patterns),
            active_interventions=active_interventions,
            horizon_cycles=horizon_cycles,
        )

        # Review gate
        review_req = self._governance.review_required(patterns, confidence)

        return TopologyEvolutionReport(
            patterns=patterns,
            lifecycle_states=lifecycle_states,
            memory_records=memory_records,
            assessment=assessment,
            sustainability=sustainability,
            governance_violations=governance_violations,
            review_required=review_req,
        )
