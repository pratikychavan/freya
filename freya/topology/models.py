"""freya/topology/models.py

Data models for the Organizational Topology Evolution Layer.

All models are Pydantic v2. IDs are short hex strings for human readability.
"""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


LifecycleStage = Literal["emerging", "recurring", "persistent", "stabilizing", "dissolving"]
RecurrenceFrequency = Literal["rare", "occasional", "frequent", "chronic"]
EvolutionState = Literal["stable", "drifting", "escalating", "chronic", "dissolving"]
ChronicInstabilityRisk = Literal["low", "moderate", "high", "critical"]
SustainabilityOutlook = Literal["resilient", "at_risk", "degrading", "critical"]


class OperationalTopologyPattern(BaseModel):
    """A recognized recurring organizational topology pattern."""

    topology_id: str = Field(default_factory=_short_id)
    topology_name: str
    recurring_partitions: list[str]
    recurring_pressure_patterns: list[str]
    recurrence_frequency: RecurrenceFrequency
    organizational_impact: str


class TopologyLifecycleState(BaseModel):
    """The maturity and lifecycle stage of an operational topology."""

    topology_name: str
    lifecycle_stage: LifecycleStage
    stabilization_maturity: str
    projected_evolution_risk: str
    dissolution_probability: float          # [0.0, 1.0]


class OperationalMemoryRecord(BaseModel):
    """A bounded historical record of a stabilization outcome."""

    record_id: str = Field(default_factory=_short_id)
    historical_pattern: str
    stabilization_outcome: str              # "effective", "partial", "failed"
    recovery_duration: str
    future_recommendation: str


class TopologyEvolutionAssessment(BaseModel):
    """Assessment of how the current operational topology is evolving."""

    evolution_state: EvolutionState
    chronic_instability_risk: ChronicInstabilityRisk
    sustainability_outlook: SustainabilityOutlook
    recommended_adaptation: str
    confidence_score: float
