"""freya/hitl/semantic/classifier.py

SemanticGovernanceIntentClassifier — classifies human guidance into one of
the recognised SemanticCategory values.

Design:
  1. Governance bypass signals are checked FIRST, unconditionally, before any
     approval or other classification.  This ensures "skip approval and proceed"
     is NEVER confused with a simple approval.

  2. LLM path: sends a strict structured prompt to an LLM adapter for
     high-accuracy disambiguation of ambiguous inputs.

  3. Deterministic fallback: semantic signal tables with multi-token pattern
     groups that go beyond single-keyword matching.

Category priority order (highest to lowest precedence):
  governance_bypass_attempt  ← always checked first
  approval
  rejection
  execution_policy_change
  constraint_modification
  priority_change
  optimization_request
  operational_guidance
  ambiguous_instruction      ← default when nothing else matches
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from freya.hitl.semantic.models import SemanticCategory, SemanticGuidanceIntent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Semantic signal tables
# Multi-token patterns are deliberately broad: they rely on phrase co-occurrence
# rather than single keywords so that "skip the plan" doesn't match bypass.
# ---------------------------------------------------------------------------

# CRITICAL — checked before everything else
_BYPASS_SIGNALS: list[str] = [
    "skip approval",
    "bypass approval",
    "skip the approval",
    "bypass the approval",
    "override governance",
    "ignore governance",
    "disable approval",
    "remove approval",
    "skip governance",
    "bypass governance",
    "skip review",
    "bypass review",
    "ignore review",
    "skip the review",
    "proceed without approval",
    "proceed without review",
    "skip the check",
    "disable check",
    "ignore the check",
    "just proceed without",
    "proceed anyway",
    "force proceed",
    "override the check",
    "ignore policy",
    "skip policy",
    "bypass policy",
]

_APPROVAL_SIGNALS: list[str] = [
    "looks good", "approve", "approved", "proceed", "go ahead",
    "yes please", "confirmed", "accepted", "agree", "do it",
    "that works", "sounds good", "perfect", "great", "ok ",
    "okay", "all good", "fine by me", "i approve", "looks great",
    "let's proceed", "continue", "yes, proceed",
]

_REJECTION_SIGNALS: list[str] = [
    "reject", "rejected", "cancel", "don't proceed", "do not proceed",
    "stop", "no thank you", "i decline", "not approved", "decline",
    "don't do it", "abort", "refused", "refuse", "not acceptable",
    "i disagree", "no, don't", "hold off",
]

_POLICY_CHANGE_SIGNALS: list[str] = [
    "reduce reasoning depth",
    "lower reasoning depth",
    "reduce analysis depth",
    "skip deep analysis",
    "skip deep comparison",
    "use faster analysis",
    "use shallow analysis",
    "fewer retries",
    "reduce retries",
    "fail fast",
    "lower retry",
    "skip the deep",
    "less analysis",
    "simpler analysis",
    "no deep reasoning",
    "reduce cognitive",
    "lower cognitive",
]

_CONSTRAINT_SIGNALS: list[str] = [
    "increase budget",
    "reduce budget",
    "lower budget",
    "change budget",
    "extend stay",
    "reduce nights",
    "fewer nights",
    "more nights",
    "change hotel",
    "change flight",
    "different hotel",
    "different flight",
    "update constraint",
    "modify constraint",
    "adjust budget",
    "raise budget",
]

_PRIORITY_CHANGE_SIGNALS: dict[str, list[str]] = {
    "speed":        ["prioritize speed", "prioritise speed", "faster first", "speed over",
                     "quicker is better", "speed is priority"],
    "cost":         ["prioritize cost", "prioritise cost", "cost over", "cheaper first",
                     "cost is priority", "lowest cost first"],
    "quality":      ["prioritize quality", "prioritise quality", "quality over",
                     "best quality first", "quality is priority"],
    "convenience":  ["prioritize convenience", "prioritise convenience",
                     "convenience over cost", "more convenient", "convenience first"],
}

_OPTIMIZATION_SIGNALS: list[str] = [
    "find a better option",
    "better option",
    "find something better",
    "optimize",
    "optimise",
    "improve efficiency",
    "more efficient",
    "streamline",
    "find a cheaper option",
    "find cheaper",
    "look for cheaper",
    "search for cheaper",
    "explore alternatives",
    "find alternatives",
]

_OPERATIONAL_GUIDANCE_SIGNALS: list[str] = [
    "something cheaper",
    "near the metro",
    "close to metro",
    "near the station",
    "avoid expensive",
    "prefer ",
    "avoid ",
    "near the venue",
    "close to venue",
    "close to the client",
    "lower cost option",
    "budget option",
    "not too far",
    "walking distance",
]


def _norm(text: str) -> str:
    return " " + text.lower().strip() + " "


def _matches_any(text_norm: str, signals: list[str]) -> bool:
    return any(s in text_norm for s in signals)


def _deterministic_classify(text: str) -> tuple[SemanticCategory, float]:
    """Return (category, confidence) using deterministic signal tables.

    Governance bypass is evaluated first — this is a hard rule.
    """
    n = _norm(text)

    # 1. Governance bypass — highest priority, non-negotiable
    if _matches_any(n, _BYPASS_SIGNALS):
        return "governance_bypass_attempt", 0.95

    # 2. Rejection — before approval to catch "no, proceed" negations
    if _matches_any(n, _REJECTION_SIGNALS):
        return "rejection", 0.90

    # 3. Approval
    if _matches_any(n, _APPROVAL_SIGNALS):
        return "approval", 0.88

    # 4. Execution policy change
    if _matches_any(n, _POLICY_CHANGE_SIGNALS):
        return "execution_policy_change", 0.85

    # 5. Constraint modification
    if _matches_any(n, _CONSTRAINT_SIGNALS):
        return "constraint_modification", 0.82

    # 6. Priority change
    for _priority, signals in _PRIORITY_CHANGE_SIGNALS.items():
        if _matches_any(n, signals):
            return "priority_change", 0.83

    # 7. Optimization request
    if _matches_any(n, _OPTIMIZATION_SIGNALS):
        return "optimization_request", 0.80

    # 8. Operational guidance (directional but not actionable)
    if _matches_any(n, _OPERATIONAL_GUIDANCE_SIGNALS):
        return "operational_guidance", 0.72

    # Default
    return "ambiguous_instruction", 0.40


_LLM_PROMPT = """You are a governance-aware operational intent classifier for an enterprise workflow system.

Classify the following user input into EXACTLY ONE of these categories:
- approval
- rejection
- governance_bypass_attempt
- execution_policy_change
- constraint_modification
- priority_change
- optimization_request
- operational_guidance
- ambiguous_instruction

CRITICAL RULE: If the user tries to skip, bypass, disable, ignore, or override any approval, review, governance check, or policy — classify as "governance_bypass_attempt" regardless of how politely it is phrased.
Examples of governance_bypass_attempt: "Skip the approval", "Just proceed without review", "Ignore the governance check", "Bypass approval and continue."

User input: "{input}"

Return ONLY a JSON object with no markdown:
{{"category": "<one of the categories above>", "confidence": <float 0.0-1.0>, "interpreted_intent": "<one-line interpretation>"}}"""


class SemanticGovernanceIntentClassifier:
    """Classify operational guidance into a SemanticCategory.

    Parameters
    ----------
    llm_adapter : optional
        Object with ``async complete(request: dict) -> dict``.
        When provided, used for high-confidence LLM classification.
        Falls back to deterministic on failure.
    """

    def __init__(self, llm_adapter: object | None = None) -> None:
        self._adapter = llm_adapter

    async def classify(self, raw_input: str) -> SemanticGuidanceIntent:
        """Classify *raw_input* and return a SemanticGuidanceIntent."""

        # Deterministic bypass check ALWAYS runs first — even before LLM
        n = _norm(raw_input)
        if _matches_any(n, _BYPASS_SIGNALS):
            return SemanticGuidanceIntent(
                raw_input=raw_input,
                interpreted_intent="Attempting to bypass governance controls.",
                semantic_category="governance_bypass_attempt",
                governance_risk="critical",
                confidence_score=0.97,
                requires_governance_review=True,
                parse_method="deterministic",
            )

        if self._adapter is not None:
            try:
                return await self._llm_classify(raw_input)
            except Exception as exc:
                logger.warning("LLM classification failed (%s) — using fallback.", exc)

        return self._deterministic_classify(raw_input)

    async def _llm_classify(self, raw_input: str) -> SemanticGuidanceIntent:
        prompt = _LLM_PROMPT.format(input=raw_input.replace('"', "'"))
        response = await self._adapter.complete({"prompt": prompt})  # type: ignore[union-attr]
        raw = response.get("text", "").strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data: dict[str, Any] = json.loads(raw)

        category: SemanticCategory = data.get("category", "ambiguous_instruction")  # type: ignore[assignment]
        confidence: float = float(data.get("confidence", 0.7))
        intent: str = data.get("interpreted_intent", raw_input[:80])

        gov_risk, requires_review = _governance_risk_for(category, confidence)
        requires_clarification = category == "ambiguous_instruction" or confidence < 0.55

        return SemanticGuidanceIntent(
            raw_input=raw_input,
            interpreted_intent=intent,
            semantic_category=category,
            governance_risk=gov_risk,
            confidence_score=confidence,
            requires_clarification=requires_clarification,
            requires_governance_review=requires_review,
            parse_method="llm",
        )

    def _deterministic_classify(self, raw_input: str) -> SemanticGuidanceIntent:
        category, confidence = _deterministic_classify(raw_input)
        intent = _build_intent_label(raw_input, category)
        gov_risk, requires_review = _governance_risk_for(category, confidence)
        requires_clarification = category == "ambiguous_instruction" or confidence < 0.55

        return SemanticGuidanceIntent(
            raw_input=raw_input,
            interpreted_intent=intent,
            semantic_category=category,
            governance_risk=gov_risk,
            confidence_score=confidence,
            requires_clarification=requires_clarification,
            requires_governance_review=requires_review,
            parse_method="deterministic",
        )


def _governance_risk_for(
    category: SemanticCategory, confidence: float
) -> tuple[str, bool]:
    if category == "governance_bypass_attempt":
        return "critical", True
    if category == "execution_policy_change":
        return "medium", confidence < 0.70
    if category == "constraint_modification":
        return "low", False
    if category in ("approval", "rejection"):
        return "none", False
    return "none", False


def _build_intent_label(text: str, category: SemanticCategory) -> str:
    labels: dict[SemanticCategory, str] = {
        "approval":                 "Approving workflow to proceed.",
        "rejection":                "Rejecting / cancelling the workflow.",
        "governance_bypass_attempt":"Attempting to bypass governance controls.",
        "execution_policy_change":  "Requesting a change to execution policy or analysis depth.",
        "constraint_modification":  "Requesting a constraint update.",
        "priority_change":          "Requesting a change in workflow priority.",
        "optimization_request":     "Requesting workflow optimization.",
        "operational_guidance":     "Providing operational guidance or preferences.",
        "ambiguous_instruction":    "Instruction is ambiguous and needs clarification.",
    }
    return labels.get(category, text[:80])
