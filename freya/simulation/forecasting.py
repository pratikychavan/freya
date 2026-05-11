"""freya/simulation/forecasting.py

SimulationForecastingEngine

Estimates projected recovery timelines and stabilization impact
across simulated intervention scenarios. Operationally grounded —
no speculative prediction theater.
"""
from __future__ import annotations

from freya.simulation.models import InterventionEffect, SimulationOutcome

# Stability improvement → pressure reduction per cycle (0–1 per-minute rate)
_STABILITY_RECOVERY_RATE: float = 0.04


class SimulationForecastingEngine:
    """Estimate recovery and stabilization projections for simulated scenarios."""

    def estimate_recovery_minutes(
        self,
        current_pressure: float,
        effect: InterventionEffect,
        window_minutes: int = 15,
    ) -> int:
        """Estimate minutes to pressure normalization after applying an intervention."""
        effective_improvement = effect.stability_improvement
        if not effect.reversibility:
            # Irreversible interventions don't naturally recover
            effective_improvement = max(effective_improvement - 0.20, 0.0)

        rate_per_min = _STABILITY_RECOVERY_RATE * (1.0 + effective_improvement)
        if rate_per_min <= 0:
            return window_minutes * 3  # worst case

        minutes = int(current_pressure / rate_per_min)
        return max(1, minutes)

    def estimate_stabilization_probability(
        self,
        current_pressure: float,
        effect: InterventionEffect,
        window_minutes: int,
    ) -> float:
        """Estimate probability that the intervention stabilizes within the window."""
        recovery = self.estimate_recovery_minutes(current_pressure, effect, window_minutes)
        if recovery <= window_minutes:
            return min(0.90, 0.55 + effect.stability_improvement * 0.40)
        # Partial stabilization
        ratio = window_minutes / max(recovery, 1)
        return round(min(ratio * 0.85, 0.85), 2)

    def estimate_disruption_likelihood(
        self,
        outcome: SimulationOutcome,
        current_pressure: float,
    ) -> float:
        """Estimate probability of a disruption event if this scenario is applied."""
        pressure_factor = current_pressure * 0.40
        impact_factors = {
            "minimal":     0.05,
            "low":         0.12,
            "moderate":    0.25,
            "significant": 0.40,
            "severe":      0.65,
        }
        impact_factor = impact_factors.get(outcome.predicted_operational_impact, 0.20)
        return round(min(pressure_factor + impact_factor * (1 - outcome.confidence_score), 1.0), 2)

    def projected_equilibrium_improvement(
        self,
        effect: InterventionEffect,
        current_pressure: float,
    ) -> str:
        """Return a human-readable equilibrium improvement estimate."""
        improvement = effect.stability_improvement
        reduced_pressure = max(0.0, current_pressure - improvement * 0.6)

        if reduced_pressure <= 0.30:
            return f"Pressure expected to fall to low levels (~{reduced_pressure:.0%}). Full equilibrium likely."
        if reduced_pressure <= 0.55:
            return f"Pressure moderated to ~{reduced_pressure:.0%}. Equilibrium partially restored."
        return f"Pressure reduced to ~{reduced_pressure:.0%}. Continued monitoring recommended."

    def recovery_narrative(
        self,
        effect: InterventionEffect,
        minutes: int,
        stabilization_probability: float,
    ) -> list[str]:
        """Build a plain-language recovery narrative for the given outcome."""
        lines = [
            f"Estimated recovery: ~{minutes} minutes.",
            f"Stabilization probability within window: {stabilization_probability:.0%}.",
        ]
        if not effect.reversibility:
            lines.append(
                "This intervention is not easily reversible. Full restoration may require manual action."
            )
        else:
            diff_map = {
                "immediate": "Recovery is immediate after pressure drops.",
                "easy":      "Recovery is straightforward and automatic.",
                "moderate":  "Moderate recovery effort required; gradual restoration expected.",
                "complex":   "Complex recovery path — phased restoration recommended.",
                "irreversible": "Recovery is not possible without manual rollback.",
            }
            lines.append(diff_map.get(effect.recovery_difficulty, "Recovery expected."))
        return lines
