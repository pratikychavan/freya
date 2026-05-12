"""freya/sequencing/models.py

Data models for the Coordination Sequencing + Adaptive Intervention Layer.

All models are Pydantic v2. IDs are short hex strings for human readability.
"""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


class CoordinationPhase(BaseModel):
    """A discrete phase in an operational stabilization sequence."""

    phase_id: str = Field(default_factory=_short_id)
    phase_name: str
    intended_effect: str
    activation_condition: str
    completion_condition: str
    reversibility: bool


class InterventionSequence(BaseModel):
    """An ordered set of coordination phases forming a stabilization strategy."""

    sequence_id: str = Field(default_factory=_short_id)
    sequence_name: str
    phases: list[str]                      # phase_name strings in order
    expected_stabilization_effect: str
    projected_recovery_profile: str
    confidence_score: float


class AdaptiveInterventionDecision(BaseModel):
    """A single adaptive decision emitted during an active coordination phase."""

    decision_id: str = Field(default_factory=_short_id)
    current_phase: str
    recommended_next_action: str
    adaptation_reason: str
    equilibrium_effect: str


class RecoveryProgression(BaseModel):
    """The current position in an operational recovery trajectory."""

    recovery_id: str = Field(default_factory=_short_id)
    recovery_stage: str                    # e.g. early_mitigation, stabilized, recovering, restoring, complete
    restoration_actions: list[str]
    projected_recovery_time: str
    stabilization_confidence: float
