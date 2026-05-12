"""freya/sequencing/phases.py

Operational Phase Management Engine.

Defines the stabilization phase catalog, evaluates transition readiness,
and prevents unstable progression between phases.
"""
from __future__ import annotations

from freya.sequencing.models import CoordinationPhase


# ---------------------------------------------------------------------------
# Phase catalog
# ---------------------------------------------------------------------------
_PHASE_CATALOG: dict[str, CoordinationPhase] = {
    "retry_stabilization": CoordinationPhase(
        phase_name="Retry Stabilization",
        intended_effect="Reduce retry amplification through governance batching",
        activation_condition="Retry spike active or governance congestion present",
        completion_condition="Retry rate below baseline; batching showing stabilizing effect",
        reversibility=True,
    ),
    "governance_recovery": CoordinationPhase(
        phase_name="Governance Recovery",
        intended_effect="Clear governance approval queue backlog",
        activation_condition="Governance congestion active; approval queue above threshold",
        completion_condition="Approval queue reduced to normal operational capacity",
        reversibility=True,
    ),
    "contention_reduction": CoordinationPhase(
        phase_name="Contention Reduction",
        intended_effect="Reduce reasoning pool contention and stabilize utilization",
        activation_condition="Operational pressure above 0.60; contention between workflows detected",
        completion_condition="Pressure below 0.50 and pool utilization consistent",
        reversibility=True,
    ),
    "restoration": CoordinationPhase(
        phase_name="Operational Restoration",
        intended_effect="Gradually restore optimization depth and full operational quality",
        activation_condition="Pressure below 0.45; no active cascades; stable or improving trend",
        completion_condition="All interventions safely tapered; optimization fully restored",
        reversibility=False,
    ),
}

# Allowed forward transitions (conservative — phases must be traversed in order).
_SAFE_TRANSITIONS: dict[str, list[str]] = {
    "retry_stabilization": ["governance_recovery", "contention_reduction"],
    "governance_recovery": ["contention_reduction", "retry_stabilization"],
    "contention_reduction": ["restoration"],
    "restoration": [],
}

# Maximum pressure at which each forward transition is considered safe.
_TRANSITION_PRESSURE_CEILINGS: dict[tuple[str, str], float] = {
    ("retry_stabilization", "governance_recovery"): 0.70,
    ("retry_stabilization", "contention_reduction"): 0.65,
    ("governance_recovery", "contention_reduction"): 0.65,
    ("governance_recovery", "retry_stabilization"): 0.70,
    ("contention_reduction", "restoration"): 0.50,
}


class OperationalPhaseManagementEngine:
    """Manages stabilization phase catalog and transition readiness."""

    def get_phase(self, phase_name: str) -> CoordinationPhase:
        """Return the CoordinationPhase for the given name.

        Falls back to a generic unknown phase rather than raising.
        """
        if phase_name in _PHASE_CATALOG:
            return _PHASE_CATALOG[phase_name]
        return CoordinationPhase(
            phase_name=phase_name.replace("_", " ").title(),
            intended_effect="Unknown phase — operational context required.",
            activation_condition="Unknown",
            completion_condition="Unknown",
            reversibility=True,
        )

    def list_phases(self) -> list[str]:
        return list(_PHASE_CATALOG.keys())

    def safe_next_phases(self, current_phase: str) -> list[str]:
        """Return the list of allowed next phases from the current one."""
        return _SAFE_TRANSITIONS.get(current_phase, [])

    def is_transition_safe(
        self,
        from_phase: str,
        to_phase: str,
        current_pressure: float,
    ) -> tuple[bool, str]:
        """Evaluate whether a phase transition is safe at the given pressure.

        Returns (is_safe, reason).
        """
        allowed = _SAFE_TRANSITIONS.get(from_phase, [])
        if to_phase not in allowed:
            return (
                False,
                f"'{to_phase}' is not a permitted successor to '{from_phase}'.",
            )

        ceiling = _TRANSITION_PRESSURE_CEILINGS.get((from_phase, to_phase))
        if ceiling is not None and current_pressure > ceiling:
            return (
                False,
                (
                    f"Pressure {current_pressure:.0%} exceeds safe ceiling {ceiling:.0%} "
                    f"for transition '{from_phase}' → '{to_phase}'."
                ),
            )

        return (True, f"Transition '{from_phase}' → '{to_phase}' is within safe bounds.")

    def recommended_phase(
        self,
        active_event_types: list[str],
        current_pressure: float,
        pressure_trend: str,
    ) -> str:
        """Recommend a phase based on active events and pressure state.

        Args:
            active_event_types: Operational events currently active.
            current_pressure: System pressure in [0.0, 1.0].
            pressure_trend: One of 'improving', 'stable', 'worsening'.
        """
        if current_pressure < 0.35 and pressure_trend in ("improving", "stable"):
            return "restoration"
        if current_pressure > 0.65 or "degradation_onset" in active_event_types:
            return "contention_reduction"
        if "governance_congestion" in active_event_types:
            return "governance_recovery"
        if "retry_spike" in active_event_types:
            return "retry_stabilization"
        if current_pressure < 0.50 and pressure_trend == "improving":
            return "restoration"
        return "contention_reduction"
