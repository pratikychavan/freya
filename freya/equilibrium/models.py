"""freya/equilibrium/models.py

Data models for the Multi-Equilibrium Operational Cognition Layer.

All models are Pydantic v2. IDs are short hex strings for human readability.
"""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


EquilibriumState = Literal["unstable", "recovering", "stabilized", "restored"]
PropagationSeverity = Literal["low", "moderate", "high"]
ReboundRisk = Literal["low", "moderate", "high"]
CoordinationRisk = Literal["low", "moderate", "high", "critical"]
GlobalStability = Literal["critical", "unstable", "mixed", "stabilizing", "stable"]


class OperationalEquilibriumZone(BaseModel):
    """The current state of a single operational equilibrium zone."""

    zone_id: str = Field(default_factory=_short_id)
    zone_name: str
    equilibrium_state: EquilibriumState
    pressure_level: float                 # [0.0, 1.0]
    stabilization_active: bool
    recovery_stage: str                   # maps to recovery engine stages


class ZonePropagationEffect(BaseModel):
    """A causal influence flowing from one zone into another."""

    source_zone: str
    target_zone: str
    propagation_effect: str
    severity: PropagationSeverity
    stabilization_impact: str


class ZoneRecoveryPlan(BaseModel):
    """A zone-specific recovery plan with staggered pacing."""

    zone_name: str
    restoration_actions: list[str]
    pacing_strategy: str
    projected_recovery_window: str
    rebound_risk: ReboundRisk


class MultiEquilibriumAssessment(BaseModel):
    """Partition-aware summary of the overall operational equilibrium state."""

    global_stability: GlobalStability
    unstable_zones: list[str]
    recovering_zones: list[str]
    stabilized_zones: list[str]
    coordination_risk: CoordinationRisk
