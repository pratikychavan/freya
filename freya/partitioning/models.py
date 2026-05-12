"""freya/partitioning/models.py

Data models for the Adaptive Organizational Partitioning Layer.

All models are Pydantic v2. IDs are short hex strings for human readability.
"""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


PartitionType = Literal[
    "incident_coordination",
    "governance_escalation",
    "optimization_backlog",
    "recovery_surge",
    "retry_amplification",
    "standard",
]

StabilizationPriority = Literal["critical", "high", "moderate", "low"]
CouplingStrength = Literal["tight", "moderate", "loose", "isolated"]
PropagationRisk = Literal["low", "moderate", "high"]
SustainabilityState = Literal["sustainable", "at_risk", "fatigued", "exhausted"]
AdaptationFatigueRisk = Literal["low", "moderate", "high", "critical"]


class OperationalPartition(BaseModel):
    """A temporary, bounded operational partition grouping related workflows."""

    partition_id: str = Field(default_factory=_short_id)
    partition_name: str
    partition_type: PartitionType
    participating_workflows: list[str]
    dominant_pressure: str
    stabilization_priority: StabilizationPriority


class PressureMigrationEvent(BaseModel):
    """Tracks movement of operational pressure from one partition to another."""

    migration_id: str = Field(default_factory=_short_id)
    source_partition: str
    target_partition: str
    migration_reason: str
    projected_operational_effect: str
    confidence_score: float


class PartitionCouplingState(BaseModel):
    """Describes the coupling relationship between two operational partitions."""

    source_partition: str
    target_partition: str
    coupling_strength: CouplingStrength
    propagation_risk: PropagationRisk
    stabilization_dependency: str


class OperationalSustainabilityAssessment(BaseModel):
    """Long-term sustainability assessment of the active stabilization strategy."""

    sustainability_state: SustainabilityState
    adaptation_fatigue_risk: AdaptationFatigueRisk
    overloaded_partitions: list[str]
    recovery_sustainability: str
    organizational_outlook: str
