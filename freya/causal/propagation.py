"""freya/causal/propagation.py

OperationalPropagationEngine

Estimates how far and how strongly an operational event propagates
through the coordination graph. Detects amplification loops and
stabilization propagation — all bounded to operational telemetry.

Propagation types detected:
  amplification  — effect grows stronger at each hop (e.g. retry loops)
  dampening      — effect weakens naturally (e.g. smoothing taking hold)
  oscillation    — effect alternates (e.g. retry/recovery cycles)
  cascade        — multiple independent paths are affected simultaneously
  stable         — no secondary propagation
"""
from __future__ import annotations

from freya.causal.models import (
    CausalPropagationChain,
    DestabilizationCascade,
    PropagationStrength,
)
import uuid

# Amplification triggers: when these event types are present together, amplification risk rises
_AMPLIFICATION_PAIRS: list[frozenset[str]] = [
    frozenset({"governance_congestion", "retry_spike"}),
    frozenset({"degradation_onset", "retry_spike"}),
    frozenset({"degradation_onset", "governance_congestion"}),
]

# Stabilization pairs: when these are active together, dampening is reinforced
_STABILIZATION_PAIRS: list[frozenset[str]] = [
    frozenset({"batching_applied", "smoothing_applied"}),
    frozenset({"reservation_applied", "batching_applied"}),
    frozenset({"optimization_suspended", "smoothing_applied"}),
]


class OperationalPropagationEngine:
    """Estimate the propagation dynamics of causal chains."""

    def estimate_spread(
        self,
        chain: CausalPropagationChain,
        active_event_types: list[str],
        current_pressure: float,
    ) -> dict:
        """Return a propagation estimate dict for a chain in context."""
        strength   = chain.propagation_strength
        chain_set  = frozenset(active_event_types)

        # Detect amplification
        is_amplifying = any(pair.issubset(chain_set) for pair in _AMPLIFICATION_PAIRS)

        # Detect stabilization reinforcement
        is_dampened   = any(pair.issubset(chain_set) for pair in _STABILIZATION_PAIRS)

        # Adjusted strength
        if is_amplifying and strength in ("amplified", "cascading"):
            effective_strength = "cascading"
        elif is_dampened and strength in ("amplified", "neutral"):
            effective_strength = "dampened"
        else:
            effective_strength = strength

        # Propagation depth: how many hops to expect
        depth_map = {"cascading": 5, "amplified": 4, "neutral": 2, "dampened": 1}
        estimated_depth = min(depth_map.get(effective_strength, 2), len(chain.propagation_steps))

        # Pressure modulates spread
        pressure_multiplier = 1.0 + max(0.0, current_pressure - 0.50) * 0.8

        return {
            "effective_strength":   effective_strength,
            "estimated_depth":      estimated_depth,
            "is_amplifying":        is_amplifying,
            "is_dampened":          is_dampened,
            "pressure_multiplier":  round(pressure_multiplier, 2),
            "propagation_severity": self._severity(effective_strength, current_pressure),
        }

    def detect_cascade(
        self,
        active_event_types: list[str],
        current_pressure: float,
        affected_workflow_count: int = 1,
    ) -> DestabilizationCascade | None:
        """Return a DestabilizationCascade if cascade conditions are met, else None."""
        chain_set  = frozenset(active_event_types)
        amplifying = [p for p in _AMPLIFICATION_PAIRS if p.issubset(chain_set)]
        if not amplifying or current_pressure < 0.60:
            return None

        trigger  = " + ".join(sorted(next(iter(amplifying))))
        depth    = min(2 + int(current_pressure * 4), 5)

        effects = [
            "Retry amplification increases reasoning pool utilization.",
            "Higher pool utilization elevates degradation risk.",
            "Degradation risk increases reprocessing demand.",
        ]
        if depth >= 4:
            effects.append("Reprocessing demand creates secondary governance congestion.")
        if depth >= 5:
            effects.append("Cascaded congestion may trigger emergency degradation across low-priority workflows.")

        mitigation = [
            "Apply governance batching to reduce approval interruptions.",
            "Activate reasoning compression for background workflows.",
            "Reserve capacity proactively for critical workflows.",
        ]
        if current_pressure >= 0.80:
            mitigation.insert(0, "Immediate smoothing recommended — cascade is active.")

        risk = "imminent" if current_pressure >= 0.80 else "high"

        return DestabilizationCascade(
            cascade_id=str(uuid.uuid4())[:8],
            trigger_event=trigger,
            projected_cascade_effects=effects[:depth],
            mitigation_recommendations=mitigation,
            equilibrium_risk=risk,  # type: ignore[arg-type]
            cascade_depth=depth,
            is_amplifying=True,
        )

    # ── Private ────────────────────────────────────────────────────────────────

    @staticmethod
    def _severity(strength: PropagationStrength, pressure: float) -> str:
        if strength == "cascading" or (strength == "amplified" and pressure >= 0.75):
            return "high"
        if strength == "amplified":
            return "moderate"
        if strength == "neutral":
            return "low"
        return "minimal"
