"""freya/hitl/semantic/confidence.py

SemanticConfidenceEngine — evaluates classification confidence and derives
behaviour (auto-apply, clarify, escalate).

Confidence tiers and their effects:

HIGH   (≥ 0.80) → apply steering safely, no interruption
MEDIUM (≥ 0.60) → apply with a brief confirmation note
LOW    (< 0.60) → require clarification before acting
VERY LOW(< 0.40)→ escalate to governance review

Additional factors that lower effective confidence:
  - Category is "ambiguous_instruction"
  - Category is "governance_bypass_attempt" (raises risk, not just confidence)
  - Short input (< 4 words): increased uncertainty
  - Input contains negation + positive signal mix (e.g. "don't skip")
"""
from __future__ import annotations

from freya.hitl.semantic.models import ConfidenceLevel, SemanticGuidanceIntent

_HIGH = 0.80
_MEDIUM = 0.60
_VERY_LOW = 0.40

# Penalty applied when input has mixed / negated signals
_NEGATION_PATTERNS = ["don't skip", "not bypass", "shouldn't skip", "i don't mean to bypass"]


def _effective_confidence(intent: SemanticGuidanceIntent) -> float:
    score = intent.confidence_score

    # Short inputs are inherently less certain
    if len(intent.raw_input.split()) < 4:
        score = max(0.0, score - 0.10)

    # Mixed negation signals — reduce confidence
    n = intent.raw_input.lower()
    if any(pat in n for pat in _NEGATION_PATTERNS):
        score = max(0.0, score - 0.15)

    # Ambiguous instruction — confidence should reflect the default
    if intent.semantic_category == "ambiguous_instruction" and score > 0.50:
        score = min(score, 0.45)

    return score


class SemanticConfidenceEngine:
    """Determine confidence level and required action for a SemanticGuidanceIntent."""

    def level(self, intent: SemanticGuidanceIntent) -> ConfidenceLevel:
        """Return the effective confidence tier."""
        eff = _effective_confidence(intent)
        if eff >= _HIGH:
            return "high"
        if eff >= _MEDIUM:
            return "medium"
        if eff >= _VERY_LOW:
            return "low"
        return "very_low"

    def requires_clarification(self, intent: SemanticGuidanceIntent) -> bool:
        lvl = self.level(intent)
        return lvl in ("low", "very_low") or intent.requires_clarification

    def requires_escalation(self, intent: SemanticGuidanceIntent) -> bool:
        lvl = self.level(intent)
        return lvl == "very_low" or intent.requires_governance_review

    def action_label(self, intent: SemanticGuidanceIntent) -> str:
        """Return a human-readable action label for the current confidence state."""
        lvl = self.level(intent)
        if intent.semantic_category == "governance_bypass_attempt":
            return "Blocked — governance bypass not permitted."
        labels = {
            "high":     "Applying guidance directly.",
            "medium":   "Applying guidance with confirmation.",
            "low":      "Clarification required before any action.",
            "very_low": "Escalating to governance review.",
        }
        return labels[lvl]

    def confidence_label(self, intent: SemanticGuidanceIntent) -> str:
        """One-word label for UI rendering."""
        labels = {"high": "High", "medium": "Medium", "low": "Low", "very_low": "Very Low"}
        return labels[self.level(intent)]
