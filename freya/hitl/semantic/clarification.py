"""freya/hitl/semantic/clarification.py

SemanticClarificationEngine — generates a ClarificationRequest for ambiguous
or low-confidence guidance inputs.

Rules:
  - One question only per ambiguity (no piling on)
  - Questions are operationally specific, not generic
  - Options are actionable workflow directives
  - Bypass attempts never receive clarification (they are blocked outright)
"""
from __future__ import annotations

from freya.hitl.semantic.models import ClarificationRequest, SemanticGuidanceIntent

# Per-category clarification templates: (question, [options])
_TEMPLATES: dict[str, tuple[str, list[str]]] = {
    "ambiguous_instruction": (
        "What would you like to optimize?",
        [
            "Reduce total cost",
            "Improve speed of execution",
            "Improve quality of results",
            "Simplify the workflow",
        ],
    ),
    "optimization_request": (
        "Which aspect should be optimised first?",
        [
            "Lower hotel and flight costs",
            "Reduce planning and analysis time",
            "Improve overall quality",
            "Keep options balanced",
        ],
    ),
    "operational_guidance": (
        "Can you clarify the specific change you need?",
        [
            "Find a lower-cost option",
            "Find an option closer to the venue",
            "Find a faster option",
            "Find a higher-quality option",
        ],
    ),
    "execution_policy_change": (
        "Which aspect of execution policy should change?",
        [
            "Reduce reasoning depth for faster results",
            "Reduce retry attempts",
            "Switch to deterministic planning mode",
            "Reduce workflow delegation depth",
        ],
    ),
    "priority_change": (
        "Which priority should take precedence?",
        [
            "Cost — lower overall spend",
            "Speed — faster execution",
            "Quality — best possible outcome",
            "Convenience — least friction",
        ],
    ),
    "constraint_modification": (
        "Which constraint should be updated?",
        [
            "Increase total budget",
            "Reduce total budget",
            "Change number of nights",
            "Change hotel tier",
        ],
    ),
}

_GENERIC_QUESTION = (
    "Could you clarify what you'd like to change about the current plan?",
    [
        "Adjust cost or budget",
        "Change priority or strategy",
        "Update preferences",
        "Modify execution settings",
    ],
)


class SemanticClarificationEngine:
    """Generate a ClarificationRequest for ambiguous guidance."""

    def needs_clarification(self, intent: SemanticGuidanceIntent) -> bool:
        """True when clarification should be requested."""
        return (
            intent.requires_clarification
            or intent.semantic_category == "ambiguous_instruction"
        ) and intent.semantic_category != "governance_bypass_attempt"

    def build(self, intent: SemanticGuidanceIntent) -> ClarificationRequest | None:
        """Return a ClarificationRequest or None if not needed."""
        if not self.needs_clarification(intent):
            return None

        question, options = _TEMPLATES.get(
            intent.semantic_category, _GENERIC_QUESTION
        )

        reason = (
            f"Your input ('{intent.raw_input[:60]}') "
            f"was interpreted as '{intent.interpreted_intent}' "
            f"but confidence is insufficient to act without verification."
        )

        return ClarificationRequest(
            reason=reason,
            clarification_question=question,
            suggested_options=options,
        )
