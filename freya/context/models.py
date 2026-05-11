"""freya/context/models.py

Core data models for the Contextual Operational Cognition layer.

These models carry workflow-scoped operational state — not conversation
history, not user preferences in the chatbot sense.  Every field is
tied to a concrete workflow execution artefact.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


GovernanceRisk = Literal["none", "low", "medium", "high", "critical"]
WorkflowMode   = Literal[
    "cost_sensitive",
    "speed_optimized",
    "quality_focused",
    "balanced",
    "governance_restricted",
    "unknown",
]
ExecutionStrategy = Literal[
    "deterministic",
    "cognitive",
    "adaptive",
    "delegated",
    "unknown",
]
DriftSeverity = Literal["none", "mild", "moderate", "severe"]


class OperationalContext(BaseModel):
    """Full snapshot of a workflow's operational + governance state."""
    workflow_id: str
    workflow_state: str                      # e.g. "planning", "executing", "completed"
    active_constraints: dict = Field(default_factory=dict)
    active_preferences: dict = Field(default_factory=dict)
    optimization_history: list[str] = Field(default_factory=list)
    governance_history:   list[str] = Field(default_factory=list)
    prior_guidance:       list[str] = Field(default_factory=list)
    operational_mode:     WorkflowMode      = "balanced"
    execution_strategy:   ExecutionStrategy = "deterministic"


class ContextualInterpretation(BaseModel):
    """Result of interpreting a user instruction through workflow context."""
    raw_input: str
    interpreted_meaning: str
    contextual_reasoning: list[str] = Field(default_factory=list)
    inferred_operational_intent: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    contextual_risk: GovernanceRisk = "none"


class OperationalTrajectory(BaseModel):
    """Distilled view of how a workflow has evolved over time."""
    trajectory_id: str
    prior_decisions: list[str]  = Field(default_factory=list)
    optimization_direction: str = "stable"
    governance_pattern: str     = "normal"
    execution_drift: str | None = None


class ContextualClarificationHint(BaseModel):
    """Prior-context-aware question to resolve ambiguity."""
    question: str
    context_reference: str       # which prior event makes this question contextual
    suggested_options: list[str] = Field(default_factory=list)
