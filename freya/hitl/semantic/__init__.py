"""freya/hitl/semantic/__init__.py

Public API for the Semantic Governance Cognition layer.

Typical usage
-------------
    from freya.hitl.semantic import SemanticGuidancePipeline
    from freya.adapters.openai import complete

    pipeline = SemanticGuidancePipeline(llm_adapter=complete)
    intent, decision, clarification = await pipeline.process("Looks good, proceed.")

The pipeline always runs in this order:
  1. Deterministic bypass check  (hard rule — before everything else)
  2. Semantic classification      (LLM if adapter available, else deterministic)
  3. Operational extraction       (constraints + preferences from text)
  4. Governance validation        (policy rules → allow / block / escalate)
  5. Confidence evaluation        (tier → action label)
  6. Clarification building       (only when confidence < "medium" or category is ambiguous)
"""
from __future__ import annotations

from typing import Callable, Awaitable

from freya.hitl.semantic.classifier import SemanticGovernanceIntentClassifier
from freya.hitl.semantic.clarification import SemanticClarificationEngine
from freya.hitl.semantic.confidence import SemanticConfidenceEngine
from freya.hitl.semantic.extractor import OperationalSemanticExtractor
from freya.hitl.semantic.governance import SemanticGovernanceValidator
from freya.hitl.semantic.models import (
    ClarificationRequest,
    GovernanceIntentDecision,
    SemanticGuidanceIntent,
)
from freya.hitl.semantic.rendering import (
    render_clarification_request,
    render_governance_decision,
    render_semantic_classification,
)

__all__ = [
    # Pipeline
    "SemanticGuidancePipeline",
    # Components
    "SemanticGovernanceIntentClassifier",
    "OperationalSemanticExtractor",
    "SemanticGovernanceValidator",
    "SemanticConfidenceEngine",
    "SemanticClarificationEngine",
    # Models
    "SemanticGuidanceIntent",
    "GovernanceIntentDecision",
    "ClarificationRequest",
    # Renderers
    "render_semantic_classification",
    "render_governance_decision",
    "render_clarification_request",
]

LLMAdapter = Callable[[dict], Awaitable[dict]]


class SemanticGuidancePipeline:
    """Wires all semantic cognition components into a single façade.

    Parameters
    ----------
    llm_adapter:
        An async callable with signature ``async (request: dict) -> dict``.
        If *None* the pipeline runs fully deterministic classification.
    """

    def __init__(self, llm_adapter: LLMAdapter | None = None) -> None:
        self._classifier = SemanticGovernanceIntentClassifier(llm_adapter=llm_adapter)
        self._extractor = OperationalSemanticExtractor()
        self._validator = SemanticGovernanceValidator()
        self._confidence = SemanticConfidenceEngine()
        self._clar_engine = SemanticClarificationEngine()

    async def process(
        self,
        raw_input: str,
    ) -> tuple[SemanticGuidanceIntent, GovernanceIntentDecision, ClarificationRequest | None]:
        """Run the full semantic governance pipeline.

        Returns
        -------
        intent:
            Classified and enriched guidance intent.
        decision:
            Governance decision (allowed / blocked / escalated).
        clarification:
            A ClarificationRequest when additional input is needed, else ``None``.
        """
        # ── 1.  Classify (bypass check is unconditionally first inside classifier) ──
        intent = await self._classifier.classify(raw_input)

        # ── 2.  Extract operational context ──────────────────────────────────────────
        if intent.semantic_category not in (
            "governance_bypass_attempt",
            "approval",
            "rejection",
        ):
            constraints, preferences = self._extractor.extract(raw_input)
            # Merge with anything the classifier already extracted
            merged_constraints = {**constraints, **intent.extracted_constraints}
            merged_preferences = {**preferences, **intent.extracted_preferences}
            intent = intent.model_copy(
                update={
                    "extracted_constraints": merged_constraints,
                    "extracted_preferences": merged_preferences,
                }
            )

        # ── 3.  Governance validation ─────────────────────────────────────────────
        decision = self._validator.validate(intent)

        # ── 4.  Confidence → clarification flags ─────────────────────────────────
        needs_clar = (
            self._confidence.requires_clarification(intent)
            or self._clar_engine.needs_clarification(intent)
        )
        needs_review = (
            self._confidence.requires_escalation(intent)
            or intent.requires_governance_review
        )
        intent = intent.model_copy(
            update={
                "requires_clarification": needs_clar,
                "requires_governance_review": needs_review,
            }
        )

        # ── 5.  Build clarification if needed ────────────────────────────────────
        # Clarification is generated even when blocked — if the block reason IS
        # ambiguity or low confidence, the clarification tells the user what to
        # provide so their instruction can be resubmitted and approved.
        clarification: ClarificationRequest | None = None
        if needs_clar:
            clarification = self._clar_engine.build(intent)

        return intent, decision, clarification

    def render(
        self,
        intent: SemanticGuidanceIntent,
        decision: GovernanceIntentDecision,
        clarification: ClarificationRequest | None,
    ) -> str:
        """Produce a combined terminal-display string for the pipeline result."""
        parts = [
            render_semantic_classification(intent),
            render_governance_decision(decision),
        ]
        if clarification is not None:
            parts.append(render_clarification_request(clarification))
        return "\n".join(parts)
