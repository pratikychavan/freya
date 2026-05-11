"""freya/hitl/semantic/models.py

Data models for the Governance Intent Classification + Semantic Guidance
Cognition layer.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# All recognised semantic categories — ordered from most to least governance-sensitive
SemanticCategory = Literal[
    "approval",
    "rejection",
    "governance_bypass_attempt",
    "execution_policy_change",
    "constraint_modification",
    "priority_change",
    "optimization_request",
    "operational_guidance",
    "ambiguous_instruction",
]

GovernanceRisk = Literal["none", "low", "medium", "high", "critical"]

ConfidenceLevel = Literal["high", "medium", "low", "very_low"]


class SemanticGuidanceIntent(BaseModel):
    """Fully interpreted semantic intent of a piece of human guidance."""

    raw_input: str
    interpreted_intent: str              # concise one-line interpretation
    semantic_category: SemanticCategory
    extracted_constraints: dict[str, Any] = Field(default_factory=dict)
    extracted_preferences: dict[str, Any] = Field(default_factory=dict)
    governance_risk: GovernanceRisk = "none"
    confidence_score: float = 0.8        # 0-1
    requires_clarification: bool = False
    requires_governance_review: bool = False
    parse_method: Literal["llm", "deterministic"] = "deterministic"


class GovernanceIntentDecision(BaseModel):
    """Governance safety verdict for a SemanticGuidanceIntent."""

    allowed: bool
    classification: SemanticCategory
    reason: str
    escalation_required: bool = False
    risk_level: GovernanceRisk = "none"


class ClarificationRequest(BaseModel):
    """Request for additional information to resolve an ambiguous intent."""

    reason: str
    clarification_question: str
    suggested_options: list[str] = Field(default_factory=list)
