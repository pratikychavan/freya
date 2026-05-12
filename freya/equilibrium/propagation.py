"""freya/equilibrium/propagation.py

Cross-Zone Propagation Engine.

Models how pressure and stabilization in one zone causally influences
adjacent zones. Remains bounded to operational telemetry — no speculative
causal world models.
"""
from __future__ import annotations

from freya.equilibrium.models import (
    OperationalEquilibriumZone,
    PropagationSeverity,
    ZonePropagationEffect,
)

# ---------------------------------------------------------------------------
# Propagation rule catalog
# (source_zone, target_zone) → (effect description, amplifying: bool)
# ---------------------------------------------------------------------------
_PROPAGATION_RULES: list[dict] = [
    # Destabilization propagation
    {
        "source": "governance",
        "target": "reasoning",
        "condition": "high_pressure",   # source pressure >= 0.60
        "propagation_effect": "Governance congestion extends approval wait times, amplifying retry demand on the reasoning pool.",
        "severity": "high",
        "stabilization_impact": "Reasoning pressure rises as governance backlog grows; retry churn directly loads the reasoning pool.",
        "direction": "destabilizing",
    },
    {
        "source": "governance",
        "target": "coordination",
        "condition": "high_pressure",
        "propagation_effect": "Governance congestion delays inter-workflow coordination, increasing coordination zone contention.",
        "severity": "moderate",
        "stabilization_impact": "Coordination throughput decreases as governance approval gates slow workflow hand-offs.",
        "direction": "destabilizing",
    },
    {
        "source": "reasoning",
        "target": "optimization",
        "condition": "high_pressure",
        "propagation_effect": "Reasoning pool saturation reduces capacity available for optimization activity.",
        "severity": "moderate",
        "stabilization_impact": "Optimization depth degrades under reasoning contention as shared capacity is reallocated.",
        "direction": "destabilizing",
    },
    {
        "source": "reasoning",
        "target": "coordination",
        "condition": "high_pressure",
        "propagation_effect": "High reasoning pressure delays response times, degrading coordination scheduling accuracy.",
        "severity": "moderate",
        "stabilization_impact": "Coordination zone experiences increased scheduling friction and throughput variability.",
        "direction": "destabilizing",
    },
    {
        "source": "optimization",
        "target": "recovery",
        "condition": "high_pressure",
        "propagation_effect": "Optimization degradation slows recovery throughput as optimization-assisted repairs are unavailable.",
        "severity": "moderate",
        "stabilization_impact": "Recovery zone pacing lengthens; manual recovery compensates for unavailable optimization paths.",
        "direction": "destabilizing",
    },
    {
        "source": "delegation",
        "target": "governance",
        "condition": "high_pressure",
        "propagation_effect": "Delegation instability elevates governance approval demand for delegated workflow hand-offs.",
        "severity": "high",
        "stabilization_impact": "Governance load increases as delegation failures require re-approval and re-routing.",
        "direction": "destabilizing",
    },
    # Stabilization spillover
    {
        "source": "governance",
        "target": "reasoning",
        "condition": "low_pressure",    # source pressure < 0.40
        "propagation_effect": "Governance stabilization reduces retry amplification, lowering reasoning pool demand.",
        "severity": "low",
        "stabilization_impact": "Reasoning zone pressure decreases as governance-driven retries are suppressed.",
        "direction": "stabilizing",
    },
    {
        "source": "reasoning",
        "target": "coordination",
        "condition": "low_pressure",
        "propagation_effect": "Reasoning stabilization improves response latency, reducing coordination zone contention.",
        "severity": "low",
        "stabilization_impact": "Coordination throughput recovers as reasoning pool pressure decreases.",
        "direction": "stabilizing",
    },
    {
        "source": "optimization",
        "target": "recovery",
        "condition": "low_pressure",
        "propagation_effect": "Optimization restoration accelerates recovery-path throughput.",
        "severity": "low",
        "stabilization_impact": "Recovery zone pacing tightens as optimization-assisted repair paths become available again.",
        "direction": "stabilizing",
    },
]


def _condition_met(source_zone: OperationalEquilibriumZone, condition: str) -> bool:
    if condition == "high_pressure":
        return source_zone.pressure_level >= 0.60
    if condition == "low_pressure":
        return source_zone.pressure_level < 0.40
    return False


def _severity_from_delta(source_pressure: float) -> PropagationSeverity:
    if source_pressure >= 0.75:
        return "high"
    if source_pressure >= 0.55:
        return "moderate"
    return "low"


class CrossZonePropagationEngine:
    """Detects and models causal influence between operational zones."""

    def detect_effects(
        self,
        zones: dict[str, OperationalEquilibriumZone],
    ) -> list[ZonePropagationEffect]:
        """Return all active cross-zone propagation effects given zone states.

        Args:
            zones: Mapping of zone_key → OperationalEquilibriumZone.
        """
        effects: list[ZonePropagationEffect] = []
        for rule in _PROPAGATION_RULES:
            source_key = rule["source"]
            target_key = rule["target"]
            if source_key not in zones or target_key not in zones:
                continue
            source_zone = zones[source_key]
            if not _condition_met(source_zone, rule["condition"]):
                continue
            severity = _severity_from_delta(source_zone.pressure_level) if rule["condition"] == "high_pressure" else "low"
            effects.append(
                ZonePropagationEffect(
                    source_zone=source_zone.zone_name,
                    target_zone=zones[target_key].zone_name,
                    propagation_effect=rule["propagation_effect"],
                    severity=severity,
                    stabilization_impact=rule["stabilization_impact"],
                )
            )
        return effects

    def highest_severity_effects(
        self, effects: list[ZonePropagationEffect]
    ) -> list[ZonePropagationEffect]:
        """Return only high-severity effects."""
        return [e for e in effects if e.severity == "high"]
