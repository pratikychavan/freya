"""freya/sequencing/recovery.py

Operational Recovery Coordination Engine.

Coordinates progressive, equilibrium-safe recovery from elevated operational
pressure. Recovery is always staged — never instant full restoration.

Recovery stages (pressure-anchored):
  early_mitigation  pressure > 0.65
  stabilized        0.45 < pressure ≤ 0.65
  recovering        0.30 < pressure ≤ 0.45
  restoring         0.15 < pressure ≤ 0.30
  complete          pressure ≤ 0.15
"""
from __future__ import annotations

from freya.sequencing.models import RecoveryProgression

# ---------------------------------------------------------------------------
# Recovery stage templates
# ---------------------------------------------------------------------------
_STAGE_TEMPLATES: dict[str, dict] = {
    "early_mitigation": {
        "restoration_actions": [
            "Apply governance batching to reduce approval interruption churn.",
            "Activate smoothing to taper background reasoning load.",
            "Defer all optimization activity until pressure below 0.60.",
            "Monitor retry rate for signs of batching effectiveness.",
        ],
        "projected_recovery_time": "Multi-cycle — pressure reduction required before recovery can begin.",
        "stabilization_confidence": 0.50,
    },
    "stabilized": {
        "restoration_actions": [
            "Maintain current batching and smoothing configuration.",
            "Reduce smoothing intensity by 10% if retry rate drops below baseline.",
            "Defer reservation unless pressure rises above 0.60 again.",
            "Begin logging recovery trajectory for governance audit.",
        ],
        "projected_recovery_time": "2–3 cycles — system stabilizing; recovery will begin once trend confirms.",
        "stabilization_confidence": 0.65,
    },
    "recovering": {
        "restoration_actions": [
            "Begin tapering batching frequency at 20% increments per cycle.",
            "Restore reasoning depth to 60% of baseline — partial restoration only.",
            "Monitor contention for rebound before each tapering increment.",
            "Defer full batching removal until pressure drops below 0.35.",
        ],
        "projected_recovery_time": "1–2 cycles — active recovery underway with conservative pacing.",
        "stabilization_confidence": 0.75,
    },
    "restoring": {
        "restoration_actions": [
            "Taper remaining batching configuration to zero.",
            "Restore reasoning depth to 90% baseline — near-full restoration.",
            "Re-enable optimization incrementally at 25% capacity per cycle.",
            "Confirm no contention rebound before completing optimization restoration.",
        ],
        "projected_recovery_time": "1 cycle — final restoration phase; monitor for rebound before completing.",
        "stabilization_confidence": 0.85,
    },
    "complete": {
        "restoration_actions": [
            "All interventions cleared — operational baseline restored.",
            "Optimization running at full depth.",
            "Governance operating at standard cadence.",
            "Recovery audit log closed.",
        ],
        "projected_recovery_time": "Complete — no further recovery actions required.",
        "stabilization_confidence": 0.95,
    },
}


def _determine_stage(pressure: float, pressure_trend: str) -> str:
    if pressure > 0.65:
        return "early_mitigation"
    if pressure > 0.45:
        return "stabilized"
    if pressure > 0.30:
        return "recovering"
    if pressure > 0.15:
        return "restoring"
    return "complete"


class OperationalRecoveryCoordinationEngine:
    """Provides staged recovery assessments anchored to current operational pressure."""

    def assess_recovery(
        self,
        current_pressure: float,
        active_interventions: list[str],
        pressure_trend: str = "stable",
    ) -> RecoveryProgression:
        """Return a RecoveryProgression for the current system state.

        Args:
            current_pressure: Operational pressure in [0.0, 1.0].
            active_interventions: Interventions currently in effect.
            pressure_trend: One of 'improving', 'stable', 'worsening'.
        """
        stage = _determine_stage(current_pressure, pressure_trend)
        template = _STAGE_TEMPLATES[stage]

        # Adjust confidence upward if trend is improving.
        confidence = template["stabilization_confidence"]
        if pressure_trend == "improving":
            confidence = min(confidence + 0.05, 0.97)
        elif pressure_trend == "worsening":
            confidence = max(confidence - 0.10, 0.20)

        # Annotate if active interventions increase recovery confidence.
        actions = list(template["restoration_actions"])
        if "batching_applied" in active_interventions and stage == "early_mitigation":
            actions.insert(0, "Batching active — governance interruption reduction confirmed.")
        if "smoothing_applied" in active_interventions and stage in ("stabilized", "recovering"):
            actions.insert(0, "Smoothing active — load curve improving toward recovery threshold.")

        return RecoveryProgression(
            recovery_stage=stage,
            restoration_actions=actions,
            projected_recovery_time=template["projected_recovery_time"],
            stabilization_confidence=round(confidence, 2),
        )

    def recovery_stage(self, current_pressure: float) -> str:
        """Return the recovery stage name for a given pressure level."""
        return _determine_stage(current_pressure, "stable")
