"""freya/topology/lifecycle.py

Topology Lifecycle Management Engine.

Tracks partition maturation through defined lifecycle stages, detects
chronic instability structures, and coordinates stabilization maturity.

Lifecycle stages (ordered):
  emerging   → first observed occurrence
  recurring  → seen multiple times (2–4)
  persistent → structurally embedded (5+)
  stabilizing → active resolution underway
  dissolving  → successfully unwinding
"""
from __future__ import annotations

from freya.topology.models import LifecycleStage, TopologyLifecycleState

# ---------------------------------------------------------------------------
# Lifecycle stage templates keyed by appearance count range
# ---------------------------------------------------------------------------
_LIFECYCLE_STAGES: list[dict] = [
    {
        "min_occurrences": 1,
        "max_occurrences": 1,
        "stage": "emerging",
        "stabilization_maturity": "Early — insufficient history for pattern validation.",
        "projected_evolution_risk": "Unknown — monitor for recurrence before classifying.",
        "dissolution_probability": 0.70,
    },
    {
        "min_occurrences": 2,
        "max_occurrences": 4,
        "stage": "recurring",
        "stabilization_maturity": "Developing — pattern confirmed; preventive action feasible.",
        "projected_evolution_risk": "Moderate — without intervention, progression to persistent likely.",
        "dissolution_probability": 0.50,
    },
    {
        "min_occurrences": 5,
        "max_occurrences": 9,
        "stage": "persistent",
        "stabilization_maturity": "Established — deep-rooted topology requiring coordinated resolution.",
        "projected_evolution_risk": "High — chronic instability risk if not actively addressed.",
        "dissolution_probability": 0.25,
    },
    {
        "min_occurrences": 10,
        "max_occurrences": 99,
        "stage": "persistent",
        "stabilization_maturity": "Chronic — topology structurally embedded in operational behavior.",
        "projected_evolution_risk": "Critical — long-term organizational sustainability impact.",
        "dissolution_probability": 0.10,
    },
]

_STABILIZING_OVERRIDE = {
    "stage": "stabilizing",
    "stabilization_maturity": "Active resolution — stabilization intervention underway.",
    "projected_evolution_risk": "Moderate — rebound risk if pacing is insufficient.",
    "dissolution_probability": 0.55,
}

_DISSOLVING_OVERRIDE = {
    "stage": "dissolving",
    "stabilization_maturity": "Dissolution confirmed — topology unwinding successfully.",
    "projected_evolution_risk": "Low — maintain pacing to complete dissolution.",
    "dissolution_probability": 0.85,
}


def _stage_for_count(occurrences: int) -> dict:
    for template in _LIFECYCLE_STAGES:
        if template["min_occurrences"] <= occurrences <= template["max_occurrences"]:
            return template
    return _LIFECYCLE_STAGES[-1]


class TopologyLifecycleManagementEngine:
    """Evaluates and tracks the lifecycle stage of an operational topology pattern."""

    def assess_lifecycle(
        self,
        topology_name: str,
        occurrence_count: int,
        stabilization_active: bool = False,
        dissolving: bool = False,
    ) -> TopologyLifecycleState:
        """Return a TopologyLifecycleState for the given topology.

        Args:
            topology_name: Human-readable topology name.
            occurrence_count: How many times this topology has been observed.
            stabilization_active: True if active resolution is in progress.
            dissolving: True if the topology is successfully unwinding.
        """
        if dissolving:
            template = _DISSOLVING_OVERRIDE
        elif stabilization_active and occurrence_count >= 2:
            template = _STABILIZING_OVERRIDE
        else:
            template = _stage_for_count(occurrence_count)

        return TopologyLifecycleState(
            topology_name=topology_name,
            lifecycle_stage=template["stage"],
            stabilization_maturity=template["stabilization_maturity"],
            projected_evolution_risk=template["projected_evolution_risk"],
            dissolution_probability=template["dissolution_probability"],
        )

    def is_chronic(self, state: TopologyLifecycleState) -> bool:
        """Return True if the topology qualifies as chronically persistent."""
        return (
            state.lifecycle_stage == "persistent"
            and state.dissolution_probability <= 0.15
        )

    def recurrence_label(self, occurrence_count: int) -> str:
        """Return a plain-language recurrence description."""
        if occurrence_count == 1:
            return "First occurrence — insufficient history"
        if occurrence_count <= 4:
            return f"Recurring ({occurrence_count} observations)"
        if occurrence_count <= 9:
            return f"Persistent ({occurrence_count} observations)"
        return f"Chronic ({occurrence_count} observations — structurally embedded)"
