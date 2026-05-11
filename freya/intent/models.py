"""freya/intent/models.py

Data models for the Intent Interpretation + Workflow Synthesis Layer.

These models sit at the boundary between human expression and runtime
orchestration — no runtime jargon is exposed to callers.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UserIntent(BaseModel):
    """The structured interpretation of a user's natural-language goal."""

    raw_input: str
    inferred_domain: str | None = None          # e.g. "business_travel"
    primary_goal: str = ""                       # normalized goal statement
    constraints: dict[str, Any] = Field(default_factory=dict)   # e.g. {"budget_inr": 40000}
    preferences: dict[str, Any] = Field(default_factory=dict)   # e.g. {"hotel_proximity": "near_venue"}
    extracted_entities: list[str] = Field(default_factory=list) # e.g. ["Bangalore", "next week"]
    ambiguity_score: float = 0.0                # 0.0 = perfectly clear, 1.0 = completely ambiguous
    requires_clarification: bool = False
    confidence: float = 1.0                     # overall extraction confidence

    def summary(self) -> str:
        parts = [f"Goal: {self.primary_goal}"]
        if self.constraints:
            parts.append("Constraints: " + ", ".join(
                f"{k}={v}" for k, v in self.constraints.items()
            ))
        if self.preferences:
            parts.append("Preferences: " + ", ".join(
                f"{k}" for k in self.preferences
            ))
        if self.extracted_entities:
            parts.append("Entities: " + ", ".join(self.extracted_entities))
        return " | ".join(parts)


class WorkflowBlueprint(BaseModel):
    """A synthesized workflow plan derived from a UserIntent.

    Describes what the runtime will do — in human terms — without
    exposing DAGs, strategies, or orchestration internals.
    """

    workflow_type: str                           # e.g. "business_travel"
    primary_goal: str                            # human-readable goal
    suggested_subworkflows: list[str] = Field(default_factory=list)   # e.g. ["Find Flights", "Compare Hotels"]
    governance_requirements: list[str] = Field(default_factory=list)  # e.g. ["budget_approval"]
    estimated_complexity: str = "moderate"       # "simple" | "moderate" | "complex"
    recommended_strategy: str = "deterministic"  # "deterministic" | "cognitive" | "hybrid"
    synthesized_goal: str = ""                   # goal string to pass to the runner
    constraints: dict[str, Any] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)
    template_id: str | None = None


class ClarificationQuestion(BaseModel):
    """A single clarification question for an ambiguous intent."""

    question: str
    reason: str                                  # why this is needed (not shown to user)
    options: list[str] | None = None             # optional structured choices
    field: str = ""                              # which intent field this resolves

    def render(self) -> str:
        lines = [f"  ❓  {self.question}"]
        if self.options:
            for i, opt in enumerate(self.options, 1):
                lines.append(f"       {i}. {opt}")
        return "\n".join(lines)


class IntentParseResult(BaseModel):
    """Full result from the intent interpretation pipeline."""

    intent: UserIntent
    blueprint: WorkflowBlueprint | None = None
    clarifications: list[ClarificationQuestion] = Field(default_factory=list)
    ready_to_execute: bool = False
    parse_method: str = "deterministic"          # "llm" | "deterministic"
