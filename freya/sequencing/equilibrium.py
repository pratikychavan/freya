"""freya/sequencing/equilibrium.py

Equilibrium Transition Engine.

Monitors phase transition stability and detects when transition pacing is
too aggressive to preserve operational equilibrium. Recommends safe pacing
adjustments without dictating outcomes.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Transition risk catalog
# ---------------------------------------------------------------------------
# (from_phase, to_phase) → (pressure_ceiling, max_safe_delta)
# pressure_ceiling: transition is risky above this pressure
# max_safe_delta:   absolute pressure drop since last cycle; faster drops are risky
_TRANSITION_RISK: dict[tuple[str, str], tuple[float, float]] = {
    ("retry_stabilization", "governance_recovery"):   (0.70, 0.15),
    ("retry_stabilization", "contention_reduction"):  (0.65, 0.15),
    ("governance_recovery", "contention_reduction"):  (0.65, 0.15),
    ("governance_recovery", "retry_stabilization"):   (0.70, 0.20),
    ("contention_reduction", "restoration"):          (0.50, 0.10),  # tightest constraint
}

_EQUILIBRIUM_RISK_LEVELS = ("low", "moderate", "high")


def _classify_risk(pressure_violation: bool, delta_violation: bool) -> str:
    if pressure_violation and delta_violation:
        return "high"
    if pressure_violation or delta_violation:
        return "moderate"
    return "low"


def _pacing_recommendation(
    risk: str,
    from_phase: str,
    to_phase: str,
    pressure: float,
    ceiling: float | None,
) -> str:
    if risk == "high":
        return (
            f"Transition '{from_phase}' → '{to_phase}' is premature. "
            f"Allow current phase to consolidate before progressing."
        )
    if risk == "moderate":
        if ceiling is not None and pressure > ceiling:
            return (
                f"Pressure {pressure:.0%} is above the safe ceiling {ceiling:.0%}. "
                f"Slow pacing — reduce pressure by at least {(pressure - ceiling):.0%} before transitioning."
            )
        return (
            f"Transition pacing is borderline. Introduce a one-cycle monitoring pause "
            f"before committing to '{to_phase}'."
        )
    return (
        f"Transition '{from_phase}' → '{to_phase}' is within safe equilibrium bounds. "
        f"Proceed at current pacing."
    )


class EquilibriumTransitionEngine:
    """Evaluates whether a phase transition preserves operational equilibrium."""

    def assess_transition(
        self,
        from_phase: str,
        to_phase: str,
        current_pressure: float,
        recent_pressure_delta: float = 0.0,
    ) -> dict:
        """Assess the equilibrium impact of a proposed phase transition.

        Args:
            from_phase: The phase being exited.
            to_phase: The phase being entered.
            current_pressure: Operational pressure in [0.0, 1.0].
            recent_pressure_delta: Pressure change since last cycle (negative = improving).

        Returns a dict with keys:
            safe_to_transition (bool)
            equilibrium_risk (str: low / moderate / high)
            pacing_recommendation (str)
            reason (str)
        """
        constraints = _TRANSITION_RISK.get((from_phase, to_phase))

        if constraints is None:
            # No specific constraint — assume moderate risk for unknown combinations.
            return {
                "safe_to_transition": False,
                "equilibrium_risk": "moderate",
                "pacing_recommendation": (
                    f"Transition '{from_phase}' → '{to_phase}' is not a recognized progression. "
                    "Verify sequencing before proceeding."
                ),
                "reason": "Unrecognized phase transition. Governance review recommended.",
            }

        ceiling, max_delta = constraints
        pressure_violation = current_pressure > ceiling
        delta_violation = abs(recent_pressure_delta) > max_delta

        risk = _classify_risk(pressure_violation, delta_violation)
        safe = risk == "low"
        pacing = _pacing_recommendation(risk, from_phase, to_phase, current_pressure, ceiling)

        reason_parts = []
        if pressure_violation:
            reason_parts.append(
                f"Pressure {current_pressure:.0%} exceeds ceiling {ceiling:.0%}."
            )
        if delta_violation:
            reason_parts.append(
                f"Recent pressure delta {abs(recent_pressure_delta):.0%} exceeds safe rate {max_delta:.0%}."
            )
        if not reason_parts:
            reason_parts.append("All transition constraints satisfied.")

        return {
            "safe_to_transition": safe,
            "equilibrium_risk": risk,
            "pacing_recommendation": pacing,
            "reason": " ".join(reason_parts),
        }

    def restoration_pace(self, current_pressure: float, confidence: float) -> str:
        """Return a plain-language restoration pacing recommendation."""
        if current_pressure > 0.45 or confidence < 0.60:
            return "Pause — pressure or confidence too low for safe restoration."
        if current_pressure > 0.35 or confidence < 0.75:
            return "Slow — 20% increments per cycle; confirm stability before each step."
        if current_pressure > 0.20:
            return "Moderate — 25% increments per cycle; monitor for contention rebound."
        return "Standard — progressive restoration within normal pacing bounds."
