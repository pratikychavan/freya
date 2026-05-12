"""freya/resilience/models.py

Data models for the Organizational Resilience & Identity Cognition Layer.

All models are Pydantic v2. Represents reserves, identity profiles,
adaptation portfolios and continuity assessments — all bounded and
fully explainable.
"""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Literal type aliases
# ---------------------------------------------------------------------------

DepletionRisk = Literal["low", "moderate", "high", "critical"]
PreservationPriority = Literal["standard", "elevated", "critical"]
RotationBalance = Literal["balanced", "skewed", "monoculture"]
ContinuityState = Literal["stable", "at_risk", "degrading", "critical"]
OperationalTrustLevel = Literal["high", "moderate", "low", "degraded"]
ResilienceOutlook = Literal["healthy", "watchlist", "concerning", "critical"]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class OperationalResilienceReserve(BaseModel):
    """Tracks the remaining adaptive capacity for a specific stabilization technique."""

    reserve_id: str = Field(default_factory=_short_id)
    reserve_type: str
    current_capacity: float                    # [0.0, 1.0]
    depletion_risk: DepletionRisk
    replenishment_strategy: str


class OrganizationalIdentityProfile(BaseModel):
    """Describes an organization's protected operating characteristics and any detected drift."""

    identity_name: str
    protected_characteristics: list[str]
    degradation_signals: list[str]
    preservation_priority: PreservationPriority


class AdaptationPortfolioState(BaseModel):
    """Describes the balance and sustainability of the active stabilization portfolio."""

    active_strategies: list[str]
    rotation_balance: RotationBalance
    overused_strategies: list[str]
    sustainability_score: float                # [0.0, 1.0]


class ContinuityAssessment(BaseModel):
    """Top-level assessment of organizational continuity under the current adaptation regime."""

    continuity_state: ContinuityState
    operational_trust_level: OperationalTrustLevel
    resilience_outlook: ResilienceOutlook
    future_recovery_capacity: str
    strategic_risk: str
