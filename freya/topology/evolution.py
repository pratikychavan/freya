"""freya/topology/evolution.py

Organizational Topology Evolution Analysis Engine.

Analyzes a collection of active topology patterns and produces a
deterministic evolution assessment. No ML — all logic is rule-based
and fully explainable.
"""
from __future__ import annotations

from freya.topology.models import (
    OperationalTopologyPattern,
    TopologyEvolutionAssessment,
)


class TopologyEvolutionAnalysisEngine:
    """Classifies the overall evolution state of a set of active topology patterns."""

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def analyze(
        self,
        patterns: list[OperationalTopologyPattern],
        confidence: float = 0.70,
    ) -> TopologyEvolutionAssessment:
        """Produce a TopologyEvolutionAssessment for the given pattern set."""
        if not patterns:
            return TopologyEvolutionAssessment(
                evolution_state="stable",
                chronic_instability_risk="low",
                sustainability_outlook="resilient",
                recommended_adaptation="No active topology patterns detected — maintain current posture.",
                confidence_score=confidence,
            )

        chronic = self.chronic_patterns(patterns)
        drift = self.detect_drift(patterns)
        frequencies = {p.recurrence_frequency for p in patterns}
        has_dissolving = any(p.recurrence_frequency == "chronic" for p in patterns)

        # Determine evolution state (priority order)
        if has_dissolving and len(chronic) >= 2:
            evolution_state = "chronic"
        elif drift and "chronic" in frequencies:
            evolution_state = "escalating"
        elif drift:
            evolution_state = "drifting"
        elif all(p.recurrence_frequency in ("rare", "occasional") for p in patterns):
            evolution_state = "stable"
        else:
            evolution_state = "drifting"

        # Determine chronic instability risk
        chronic_count = len(chronic)
        if chronic_count == 0:
            chronic_risk = "low"
        elif chronic_count == 1:
            chronic_risk = "moderate"
        elif chronic_count == 2:
            chronic_risk = "high"
        else:
            chronic_risk = "critical"

        # Determine sustainability outlook
        if evolution_state == "stable" and chronic_risk == "low":
            sustainability_outlook = "resilient"
        elif evolution_state in ("stable", "drifting") and chronic_risk in ("low", "moderate"):
            sustainability_outlook = "at_risk"
        elif evolution_state in ("escalating", "drifting") or chronic_risk == "high":
            sustainability_outlook = "degrading"
        else:
            sustainability_outlook = "critical"

        recommended_adaptation = self._recommend(
            evolution_state, chronic_risk, sustainability_outlook, chronic, patterns
        )

        return TopologyEvolutionAssessment(
            evolution_state=evolution_state,
            chronic_instability_risk=chronic_risk,
            sustainability_outlook=sustainability_outlook,
            recommended_adaptation=recommended_adaptation,
            confidence_score=confidence,
        )

    def detect_drift(self, patterns: list[OperationalTopologyPattern]) -> bool:
        """Return True if any pattern is at frequent or chronic recurrence frequency."""
        return any(p.recurrence_frequency in ("frequent", "chronic") for p in patterns)

    def chronic_patterns(
        self, patterns: list[OperationalTopologyPattern]
    ) -> list[OperationalTopologyPattern]:
        """Return all patterns classified as chronic recurrence."""
        return [p for p in patterns if p.recurrence_frequency == "chronic"]

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _recommend(
        self,
        evolution_state: str,
        chronic_risk: str,
        sustainability_outlook: str,
        chronic: list[OperationalTopologyPattern],
        all_patterns: list[OperationalTopologyPattern],
    ) -> str:
        if evolution_state == "stable":
            return (
                "Operational topology is stable. Continue periodic lifecycle reviews. "
                "No immediate intervention required."
            )
        if evolution_state == "chronic":
            chronic_names = ", ".join(p.topology_name for p in chronic)
            return (
                f"Chronic instability detected in: {chronic_names}. "
                "Escalate to root-cause structural review. "
                "Evaluate partition realignment or workflow rerouting before next cycle."
            )
        if evolution_state == "escalating":
            drift_names = ", ".join(
                p.topology_name for p in all_patterns if p.recurrence_frequency in ("frequent", "chronic")
            )
            return (
                f"Escalating drift detected: {drift_names}. "
                "Activate adaptive intervention — apply batching or sequencing adjustments. "
                "Prioritize governance review if confidence is below threshold."
            )
        if evolution_state == "drifting":
            return (
                "Topology drift is active. Apply targeted stabilization to frequently recurring "
                "patterns. Increase monitoring cadence and review partitioning boundaries."
            )
        return "Review topology patterns and apply stabilization as needed."
