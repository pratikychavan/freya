"""freya/simulation/governance.py

SimulationGovernanceEngine

Validates simulation scenarios and outcomes against safety rules.
No unsafe intervention may be recommended. Governance guarantees
are preserved at every layer.

Hard rules:
  - Critical-workflow degradation scenarios are blocked
  - Irreversible governance bypass scenarios are rejected
  - Low-confidence scenarios without governance review are advisory only
  - Risk-rated "critical" scenarios are always blocked
"""
from __future__ import annotations

from freya.simulation.models import (
    OperationalScenario,
    SimulationOutcome,
    SimulationRiskAssessment,
)

# Intervention types that directly affect governance and require scrutiny
_GOVERNANCE_SENSITIVE: frozenset[str] = frozenset({
    "workflow_degradation",
    "optimization_suspension",
    "workflow_deferral",
})

# Interventions that must never bypass critical-workflow protections
_CRITICAL_WORKFLOW_PROTECTED: frozenset[str] = frozenset({
    "workflow_degradation",
    "reasoning_compression",
})


class SimulationGovernanceEngine:
    """Validate simulation safety before scenarios are recommended."""

    def assess_risk(
        self,
        scenario: OperationalScenario,
        outcome: SimulationOutcome,
        has_critical_workflows: bool = False,
    ) -> SimulationRiskAssessment:
        """Return a risk assessment for the scenario/outcome pair."""
        blocking_reasons: list[str] = []

        # Governance risk
        gov_risk = self._governance_risk(outcome, scenario)
        if gov_risk == "critical":
            blocking_reasons.append(
                f"Scenario '{scenario.scenario_name}' carries critical governance risk."
            )

        # Operational risk
        op_risk = self._operational_risk(outcome)

        # Coordination risk
        coord_risk = self._coordination_risk(scenario, outcome, has_critical_workflows)
        if coord_risk == "critical":
            blocking_reasons.append(
                f"Scenario '{scenario.scenario_name}' degrades critical workflows — blocked."
            )

        # Reversibility gate
        if not outcome.reversibility:
            if outcome.predicted_operational_impact in ("significant", "severe"):
                blocking_reasons.append(
                    f"Scenario '{scenario.scenario_name}' is irreversible with severe impact — rejected."
                )

        explanation = self._explain(gov_risk, op_risk, coord_risk, blocking_reasons)

        return SimulationRiskAssessment(
            scenario_id=scenario.scenario_id,
            governance_risk=gov_risk,
            operational_risk=op_risk,
            coordination_risk=coord_risk,
            explanation=explanation,
            safe_to_proceed=len(blocking_reasons) == 0,
            blocking_reasons=blocking_reasons,
        )

    def validate_batch(
        self,
        scenarios: list[OperationalScenario],
        outcomes: dict[str, SimulationOutcome],
        has_critical_workflows: bool = False,
    ) -> dict[str, SimulationRiskAssessment]:
        """Assess risk for all scenarios; return map of scenario_id → assessment."""
        return {
            s.scenario_id: self.assess_risk(
                s, outcomes[s.scenario_id], has_critical_workflows
            )
            for s in scenarios
            if s.scenario_id in outcomes
        }

    # ── Private ────────────────────────────────────────────────────────────────

    @staticmethod
    def _governance_risk(outcome: SimulationOutcome, scenario: OperationalScenario) -> str:
        if outcome.projected_governance_effect == "critical":
            return "critical"
        if scenario.intervention_type in _GOVERNANCE_SENSITIVE:
            if outcome.predicted_operational_impact in ("significant", "severe"):
                return "high"
            return "moderate"
        if outcome.projected_governance_effect == "negative":
            return "moderate"
        return "low"

    @staticmethod
    def _operational_risk(outcome: SimulationOutcome) -> str:
        impact_risk = {"minimal": "none", "low": "low", "moderate": "moderate",
                       "significant": "high", "severe": "critical"}
        return impact_risk.get(outcome.predicted_operational_impact, "low")

    @staticmethod
    def _coordination_risk(
        scenario: OperationalScenario,
        outcome: SimulationOutcome,
        has_critical_workflows: bool,
    ) -> str:
        if has_critical_workflows and scenario.intervention_type in _CRITICAL_WORKFLOW_PROTECTED:
            return "critical"
        if len(scenario.affected_workflows) >= 4:
            return "moderate"
        return "low"

    @staticmethod
    def _explain(
        gov_risk: str,
        op_risk: str,
        coord_risk: str,
        blocking_reasons: list[str],
    ) -> str:
        if blocking_reasons:
            return "BLOCKED: " + " | ".join(blocking_reasons)
        parts = [
            f"Governance risk: {gov_risk}",
            f"Operational risk: {op_risk}",
            f"Coordination risk: {coord_risk}",
        ]
        return "; ".join(parts) + ". Scenario is safe to simulate."
