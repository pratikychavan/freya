"""freya/context/cognition.py

ContextualOperationalCognitionEngine

Interprets user guidance in the light of workflow history, operational state,
and governance trajectory.

Design rules:
  - Deterministic-first: keyword + context analysis runs before any LLM call
  - LLM used only when context ambiguity is high
  - Never exposed as conversational AI — always operational
  - No chain-of-thought exposed in outputs
"""
from __future__ import annotations

import json
import re
from typing import Callable, Awaitable

from freya.context.history import WorkflowHistoryEngine
from freya.context.models import ContextualInterpretation, OperationalContext

LLMAdapter = Callable[[dict], Awaitable[dict]]

# ── Preference → operational mode heuristics ─────────────────────────────────
_COST_KW     = ("cheaper", "cost", "budget", "save", "affordable", "reduce cost", "lower cost")
_SPEED_KW    = ("faster", "speed", "quick", "less time", "hurry")
_QUALITY_KW  = ("quality", "better", "premium", "higher standard", "improve")
_LOCATION_KW = ("metro", "proximity", "near", "close", "convenient location", "access")


class ContextualOperationalCognitionEngine:
    """Interprets guidance contextually using workflow operational state."""

    def __init__(self, llm_adapter: LLMAdapter | None = None) -> None:
        self._llm = llm_adapter
        self._history_engine = WorkflowHistoryEngine()

    # ── Primary API ───────────────────────────────────────────────────────────

    async def interpret(
        self,
        raw_input: str,
        ctx: OperationalContext,
    ) -> ContextualInterpretation:
        """Return a ContextualInterpretation grounded in workflow history."""
        # Always run deterministic first
        det = self._deterministic_interpret(raw_input, ctx)

        # Escalate to LLM only when confidence is low AND adapter is available
        if det.confidence_score < 0.60 and self._llm is not None:
            try:
                return await self._llm_interpret(raw_input, ctx)
            except Exception:
                pass  # graceful fallback

        return det

    # ── Deterministic interpretation ─────────────────────────────────────────

    def _deterministic_interpret(
        self,
        raw: str,
        ctx: OperationalContext,
    ) -> ContextualInterpretation:
        lower = raw.lower()
        reasoning: list[str] = []
        intent_parts: list[str] = []
        risk = "none"
        confidence = 0.72

        # ── Cost guidance ────────────────────────────────────────────────────
        if any(kw in lower for kw in _COST_KW):
            # Check if location preference was previously set
            prefers_location = ctx.active_preferences.get("metro_access") or ctx.active_preferences.get(
                "hotel_proximity"
            )
            if prefers_location:
                intent_parts.append(
                    "reduce cost while preserving location preference (metro/proximity)"
                )
                reasoning.append(
                    "Prior guidance established metro/location preference — cost reduction "
                    "should not sacrifice this constraint."
                )
                confidence = 0.84
            else:
                intent_parts.append("reduce overall cost")
                reasoning.append("No prior location preference — generic cost reduction applies.")
                confidence = 0.78

            # Prior optimization history
            if any("cost" in o.lower() for o in ctx.optimization_history):
                reasoning.append(
                    "Workflow has already been optimized for cost — further reductions may "
                    "require trade-offs with quality or convenience."
                )
                confidence = min(confidence, 0.70)
                risk = "low"

        # ── Speed guidance ───────────────────────────────────────────────────
        elif any(kw in lower for kw in _SPEED_KW):
            intent_parts.append("optimize for faster execution")
            reasoning.append("User requested speed improvement.")
            if "speed_optimized" in ctx.operational_mode:
                reasoning.append("Workflow already in speed-optimized mode; effect may be limited.")
                risk = "low"
                confidence = 0.68
            else:
                confidence = 0.80

        # ── Quality guidance ─────────────────────────────────────────────────
        elif any(kw in lower for kw in _QUALITY_KW):
            intent_parts.append("improve output quality")
            reasoning.append("User requested quality improvement.")
            if ctx.active_constraints.get("budget_delta", 0) < 0:
                reasoning.append(
                    "Active cost constraint detected — quality improvement may conflict with budget."
                )
                risk = "medium"
                confidence = 0.65
            else:
                confidence = 0.80

        # ── Location / convenience guidance ──────────────────────────────────
        elif any(kw in lower for kw in _LOCATION_KW):
            intent_parts.append("preserve or enhance location convenience")
            reasoning.append("User guidance references location or access preferences.")
            confidence = 0.82

        # ── Fallback: ambiguous ───────────────────────────────────────────────
        else:
            intent_parts.append("general operational adjustment (intent unclear)")
            reasoning.append("Input did not match known operational patterns.")
            confidence = 0.42

        # ── Contextual enrichment ─────────────────────────────────────────────
        if ctx.governance_history:
            bypass_count = sum(
                1 for g in ctx.governance_history
                if "bypass" in g.lower() or "blocked" in g.lower()
            )
            if bypass_count >= 2:
                reasoning.append(
                    f"Workflow has {bypass_count} governance conflicts — guidance will be "
                    "evaluated under heightened scrutiny."
                )
                risk = max(risk, "medium", key=lambda r: ["none","low","medium","high","critical"].index(r))

        interpreted = "; ".join(intent_parts) if intent_parts else "operational adjustment"

        return ContextualInterpretation(
            raw_input=raw,
            interpreted_meaning=interpreted,
            contextual_reasoning=reasoning,
            inferred_operational_intent=interpreted,
            confidence_score=round(confidence, 2),
            contextual_risk=risk,
        )

    # ── LLM interpretation ────────────────────────────────────────────────────

    async def _llm_interpret(
        self,
        raw: str,
        ctx: OperationalContext,
    ) -> ContextualInterpretation:
        history_block = self._history_engine.as_context_block(ctx)
        prompt = f"""You are an operational cognition engine for an agentic workflow system.
Your sole job is to interpret a user instruction using workflow operational context.

OPERATIONAL CONTEXT:
  Workflow Mode: {ctx.operational_mode}
  Active Constraints: {ctx.active_constraints}
  Active Preferences: {ctx.active_preferences}
  Recent History:
{history_block}

USER INSTRUCTION: "{raw}"

Respond with ONLY this JSON (no markdown, no explanation):
{{
  "interpreted_meaning": "<one-sentence operational interpretation>",
  "contextual_reasoning": ["<reason 1>", "<reason 2>"],
  "inferred_operational_intent": "<concise intent label>",
  "confidence_score": <0.0-1.0>,
  "contextual_risk": "<none|low|medium|high|critical>"
}}"""

        response = await self._llm({"prompt": prompt})
        text = response.get("text", "")
        # Strip markdown fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        return ContextualInterpretation(
            raw_input=raw,
            interpreted_meaning=data["interpreted_meaning"],
            contextual_reasoning=data.get("contextual_reasoning", []),
            inferred_operational_intent=data["inferred_operational_intent"],
            confidence_score=float(data["confidence_score"]),
            contextual_risk=data.get("contextual_risk", "none"),
        )
