"""freya/hitl/interpreter.py

HumanGuidanceInterpreter — parses free-form operational guidance into a
structured HumanGuidance with typed intent, constraints and preferences.

Two paths:
  1. LLM-powered  : uses an LLM adapter for high-accuracy interpretation.
  2. Deterministic: keyword/regex heuristics — always available as fallback.

Guidance types detected:
  cost_adjustment         "find cheaper" / "reduce cost" / "lower budget"
  priority_change         "prioritise speed/quality/cost/convenience"
  preference_update       "avoid X" / "prefer Y" / "closer to Z"
  governance_override_req "skip approval" / "bypass review"
  optimization_request    "optimise" / "improve efficiency"
  execution_depth_change  "skip deep comparison" / "faster analysis"
  recovery_policy_change  "fewer retries" / "fail fast"
  approve                 "approve" / "yes" / "proceed"
  reject                  "reject" / "no" / "cancel"
  unknown                 anything else
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from freya.hitl.models import GuidanceType, HumanGuidance

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Deterministic signal tables
# ---------------------------------------------------------------------------

_COST_SIGNALS = [
    "cheaper", "lower cost", "reduce cost", "less expensive", "budget",
    "save money", "economical", "affordable", "cut cost", "cheaper option",
    "lower price", "lower budget", "cost less",
]
_PRIORITY_SIGNALS = {
    "speed":       ["faster", "quickest", "asap", "urgent", "speed", "quickly"],
    "quality":     ["better quality", "premium", "best", "top tier", "high quality"],
    "cost":        ["lowest cost", "cheapest", "most affordable"],
    "convenience": ["convenient", "easy", "simple", "comfortable"],
}
_PREFERENCE_SIGNALS = {
    "avoid":    [r"avoid (.+)", r"no (.+)", r"don't use (.+)", r"skip (.+)"],
    "prefer":   [r"prefer (.+)", r"closer to (.+)", r"near (.+)", r"adjacent to (.+)"],
    "metro":    ["metro", "subway", "transit", "public transport"],
    "venue":    ["venue", "office", "client", "meeting"],
}
_GOV_OVERRIDE_SIGNALS = [
    "skip approval", "bypass review", "override governance",
    "remove approval", "disable check", "skip governance",
]
_OPTIMIZATION_SIGNALS = [
    "optimise", "optimize", "improve efficiency", "better option",
    "more efficient", "streamline",
]
_DEPTH_CHANGE_SIGNALS = [
    "skip deep", "fast analysis", "quick comparison", "skip comparison",
    "shallow", "no deep", "simpler analysis",
]
_RECOVERY_SIGNALS = [
    "fewer retries", "fail fast", "stop retrying", "reduce retries",
    "fewer attempts", "give up faster",
]
_APPROVE_SIGNALS = [
    "approve", "yes", "proceed", "ok", "okay", "go ahead", "confirmed",
    "accept", "agree", "do it",
]
_REJECT_SIGNALS = [
    "reject", "no", "cancel", "stop", "decline", "refuse", "don't proceed",
    "do not proceed",
]


def _normalize(text: str) -> str:
    return text.lower().strip()


def _classify_type(text: str) -> GuidanceType:
    n = _normalize(text)
    if any(s in n for s in _APPROVE_SIGNALS):
        return "approve"
    if any(s in n for s in _REJECT_SIGNALS):
        return "reject"
    if any(s in n for s in _GOV_OVERRIDE_SIGNALS):
        return "governance_override_request"
    if any(s in n for s in _RECOVERY_SIGNALS):
        return "recovery_policy_change"
    if any(s in n for s in _DEPTH_CHANGE_SIGNALS):
        return "execution_depth_change"
    if any(s in n for s in _OPTIMIZATION_SIGNALS):
        return "optimization_request"
    for _priority, signals in _PRIORITY_SIGNALS.items():
        if any(s in n for s in signals):
            return "priority_change"
    if any(s in n for s in _COST_SIGNALS):
        return "cost_adjustment"
    # preference: "avoid X" / "prefer Y" / "near X"
    all_pref_patterns = [p for pats in _PREFERENCE_SIGNALS.values() for p in pats]
    for pat in all_pref_patterns:
        if re.search(pat, n):
            return "preference_update"
    return "unknown"


def _extract_constraints(text: str) -> dict[str, Any]:
    n = _normalize(text)
    constraints: dict[str, Any] = {}

    # Budget delta: "₹5,000 cheaper" / "₹3k less" / "reduce by 10%"
    budget_m = re.search(r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*)\s*([kKlL]?)", n)
    if budget_m:
        val = float(budget_m.group(1).replace(",", ""))
        unit = budget_m.group(2).lower()
        if unit == "k":
            val *= 1_000
        elif unit == "l":
            val *= 100_000
        constraints["budget_target"] = int(val)

    # Retry reduction
    retry_m = re.search(r"(\d+)\s*retr(?:y|ies)", n)
    if retry_m:
        constraints["max_retries"] = int(retry_m.group(1))

    return constraints


def _extract_preferences(text: str) -> dict[str, Any]:
    n = _normalize(text)
    prefs: dict[str, Any] = {}

    # Avoid patterns
    for pat in _PREFERENCE_SIGNALS["avoid"]:
        m = re.search(pat, n)
        if m:
            prefs["avoid"] = m.group(1).strip()
            break

    # Prefer patterns
    for pat in _PREFERENCE_SIGNALS["prefer"]:
        m = re.search(pat, n)
        if m:
            prefs["prefer"] = m.group(1).strip()
            break

    # Convenience signals
    if any(s in n for s in _PREFERENCE_SIGNALS["metro"]):
        prefs["metro_access"] = True
    if any(s in n for s in _PREFERENCE_SIGNALS["venue"]):
        prefs["venue_proximity"] = True

    # Priority signals
    for priority, signals in _PRIORITY_SIGNALS.items():
        if any(s in n for s in signals):
            prefs["priority"] = priority
            break

    return prefs


def _build_intent(text: str, guidance_type: GuidanceType) -> str:
    n = _normalize(text)
    labels = {
        "cost_adjustment": "Reduce trip cost",
        "priority_change": "Change execution priority",
        "preference_update": "Update operational preferences",
        "governance_override_request": "Request governance override",
        "optimization_request": "Request workflow optimization",
        "execution_depth_change": "Adjust analysis depth",
        "recovery_policy_change": "Modify recovery policy",
        "approve": "Approve current proposal",
        "reject": "Reject current proposal",
        "unknown": "Unclassified operational guidance",
    }
    base = labels.get(guidance_type, "Operational guidance")
    # Append key fragment from raw
    fragment = text[:60].strip()
    if len(fragment) > 20:
        return f"{base}: \"{fragment}\""
    return base


class HumanGuidanceInterpreter:
    """Parse raw user text into a structured HumanGuidance.

    Parameters
    ----------
    llm_adapter : optional
        Object with ``async complete(request: dict) -> dict``.
        When provided, used for LLM-powered interpretation.
    """

    def __init__(self, llm_adapter: object | None = None) -> None:
        self._adapter = llm_adapter

    async def interpret(self, raw_input: str) -> HumanGuidance:
        if self._adapter is not None:
            try:
                return await self._llm_interpret(raw_input)
            except Exception as exc:
                logger.warning("LLM guidance interpretation failed (%s) — fallback.", exc)
        return self._deterministic_interpret(raw_input)

    # ── LLM path ──────────────────────────────────────────────────────

    async def _llm_interpret(self, raw_input: str) -> HumanGuidance:
        prompt = f"""You are an operational workflow guidance parser.

The user is interacting with a workflow during execution and has provided operational guidance.

User input: "{raw_input}"

Classify this guidance into a JSON object with:
{{
  "guidance_type": "<cost_adjustment|priority_change|preference_update|governance_override_request|optimization_request|execution_depth_change|recovery_policy_change|approve|reject|unknown>",
  "interpreted_intent": "<one-sentence operational interpretation>",
  "extracted_constraints": {{"budget_target": <number or null>, "max_retries": <number or null>}},
  "extracted_preferences": {{"avoid": "<string or null>", "prefer": "<string or null>", "priority": "<cost|speed|quality|convenience or null>"}},
  "confidence_score": <0.0-1.0>,
  "requires_governance_review": <true/false>
}}

Only return the JSON object. No markdown."""

        response = await self._adapter.complete({"prompt": prompt})
        raw = response.get("text", "").strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        data = json.loads(raw)

        constraints = {k: v for k, v in data.get("extracted_constraints", {}).items() if v is not None}
        preferences = {k: v for k, v in data.get("extracted_preferences", {}).items() if v is not None}

        return HumanGuidance(
            guidance_id=uuid.uuid4().hex[:8],
            raw_input=raw_input,
            interpreted_intent=data.get("interpreted_intent", raw_input[:80]),
            guidance_type=data.get("guidance_type", "unknown"),
            extracted_constraints=constraints,
            extracted_preferences=preferences,
            confidence_score=float(data.get("confidence_score", 0.8)),
            requires_governance_review=bool(data.get("requires_governance_review", False)),
            parse_method="llm",
        )

    # ── Deterministic path ────────────────────────────────────────────

    def _deterministic_interpret(self, raw_input: str) -> HumanGuidance:
        guidance_type = _classify_type(raw_input)
        constraints = _extract_constraints(raw_input)
        preferences = _extract_preferences(raw_input)
        intent = _build_intent(raw_input, guidance_type)

        requires_gov_review = guidance_type == "governance_override_request"
        confidence = 0.9 if guidance_type in ("approve", "reject") else 0.75

        return HumanGuidance(
            guidance_id=uuid.uuid4().hex[:8],
            raw_input=raw_input,
            interpreted_intent=intent,
            guidance_type=guidance_type,
            extracted_constraints=constraints,
            extracted_preferences=preferences,
            confidence_score=confidence,
            requires_governance_review=requires_gov_review,
            parse_method="deterministic",
        )
