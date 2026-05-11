"""freya/intent/interpreter.py

Parses natural-language user input into a structured UserIntent.

Two modes:
  1. LLM-powered  — uses an LLM adapter to extract structured intent via a
     JSON-returning prompt. More accurate for complex, multi-entity inputs.
  2. Deterministic — regex + heuristic extraction. No LLM required.
     Always available as a fallback.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from freya.intent.classifier import IntentClassifier
from freya.intent.models import UserIntent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Deterministic extraction patterns
# ---------------------------------------------------------------------------

# Budget — matches ₹40k, ₹40,000, 40000 INR, Rs 40k, budget 40k, etc.
_BUDGET_PATTERNS = [
    re.compile(r"(?:budget|under|within|max(?:imum)?|limit(?:ed to)?|₹|rs\.?|inr)\s*[\s:of]*"
               r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*([kKlL]?)", re.I),
    re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*([kKlL]?)\s*(?:₹|inr|rupees?)", re.I),
]

_NIGHTS_PATTERNS = [
    re.compile(r"(\d+)\s*(?:-\s*)?(?:night|day)s?", re.I),
]

_CITY_NAMES = {
    "bangalore", "bengaluru", "mumbai", "bombay", "delhi", "new delhi",
    "hyderabad", "chennai", "madras", "pune", "kolkata", "calcutta",
    "gurgaon", "gurugram", "noida", "ahmedabad", "jaipur", "lucknow",
    # International
    "london", "new york", "singapore", "dubai", "san francisco", "tokyo",
}

_PREFERENCE_SIGNALS: dict[str, list[str]] = {
    "hotel_proximity": ["near", "close to", "proximity", "walking distance", "adjacent"],
    "budget_conscious": ["cheap", "affordable", "economy", "budget", "lowest cost", "cheapest"],
    "premium": ["luxury", "5 star", "five star", "premium", "business class", "first class"],
    "speed": ["fast", "earliest", "quickest", "urgent", "asap", "immediately"],
    "flexibility": ["flexible", "any time", "open", "no preference"],
}


def _parse_amount(value: str, unit: str) -> int:
    """Parse numeric amount, expanding k/K → *1000, L/l → *100000."""
    try:
        num = float(value.replace(",", ""))
        unit = unit.strip().lower()
        if unit in ("k",):
            num *= 1_000
        elif unit in ("l",):
            num *= 100_000
        return int(num)
    except ValueError:
        return 0


def _extract_budget(text: str) -> int | None:
    for pattern in _BUDGET_PATTERNS:
        m = pattern.search(text)
        if m:
            amount = _parse_amount(m.group(1), m.group(2) if len(m.groups()) > 1 else "")
            if amount > 0:
                return amount
    return None


def _extract_nights(text: str) -> int | None:
    for pattern in _NIGHTS_PATTERNS:
        m = pattern.search(text)
        if m:
            return int(m.group(1))
    return None


def _extract_cities(text: str) -> list[str]:
    text_lower = text.lower()
    found: list[str] = []
    for city in _CITY_NAMES:
        if city in text_lower:
            found.append(city.title())
    # Also catch capitalised words that look like city names (fallback)
    caps = re.findall(r"\b[A-Z][a-z]{3,}\b", text)
    for word in caps:
        if word.lower() not in {c.lower() for c in found}:
            found.append(word)
    return list(dict.fromkeys(found))   # preserve order, deduplicate


def _extract_preferences(text: str) -> dict[str, Any]:
    text_lower = text.lower()
    prefs: dict[str, Any] = {}
    for pref_key, signals in _PREFERENCE_SIGNALS.items():
        if any(sig in text_lower for sig in signals):
            prefs[pref_key] = True
    return prefs


def _infer_goal(text: str, domain: str | None) -> str:
    """Build a concise goal string from the input."""
    cities = _extract_cities(text)
    destination = cities[0] if cities else None

    if domain == "business_travel":
        nights = _extract_nights(text)
        budget = _extract_budget(text)
        parts = ["Plan a business trip"]
        if destination:
            parts[0] += f" to {destination}"
        if nights:
            parts.append(f"{nights} nights")
        if budget:
            parts.append(f"budget ₹{budget:,}")
        goal = " · ".join(parts)
        return goal
    if domain == "incident_response":
        return f"Coordinate incident response: {text[:80]}"
    if domain == "data_pipeline":
        return "Orchestrate data pipeline"
    if domain == "scheduling":
        return "Schedule and coordinate meeting"
    if domain == "procurement":
        return f"Process procurement request: {text[:80]}"
    # Generic fallback
    return text[:120]


def _compute_ambiguity(text: str, domain: str | None, constraints: dict, entities: list) -> float:
    """Heuristic ambiguity score [0, 1]."""
    score = 0.0
    if domain is None:
        score += 0.5
    if not entities:
        score += 0.2
    if not constraints:
        score += 0.15
    # Short inputs are usually more ambiguous
    if len(text.split()) < 5:
        score += 0.15
    return min(score, 1.0)


class IntentInterpreter:
    """Parses user input into a structured UserIntent.

    Parameters
    ----------
    llm_adapter : optional
        Any object implementing ``async complete(request: dict) -> dict``.
        When provided, used for LLM-powered extraction.
        When None, falls back to deterministic parsing.
    """

    def __init__(self, llm_adapter: object | None = None) -> None:
        self._adapter = llm_adapter
        self._classifier = IntentClassifier()

    async def interpret(self, raw_input: str) -> UserIntent:
        """Parse raw_input and return a structured UserIntent."""
        domain, confidence = self._classifier.classify(raw_input)

        if self._adapter is not None:
            try:
                return await self._llm_interpret(raw_input, domain, confidence)
            except Exception as exc:
                logger.warning("LLM intent interpretation failed (%s) — using fallback.", exc)

        return self._deterministic_interpret(raw_input, domain, confidence)

    # ── LLM path ──────────────────────────────────────────────────────

    async def _llm_interpret(
        self, raw_input: str, domain: str | None, confidence: float
    ) -> UserIntent:
        prompt = f"""You are an operational intent parser. Extract structured information from this user request.

User request: "{raw_input}"
Suspected domain: {domain or "unknown"}

Return a JSON object with these fields:
{{
  "primary_goal": "<concise goal statement, 1 sentence>",
  "inferred_domain": "<one of: business_travel, incident_response, data_pipeline, scheduling, procurement, or null>",
  "constraints": {{
    "budget_inr": <number or null>,
    "nights": <number or null>,
    "deadline": "<string or null>"
  }},
  "preferences": {{
    "hotel_proximity": <true/false>,
    "budget_conscious": <true/false>,
    "premium": <true/false>
  }},
  "extracted_entities": ["<entity1>", "<entity2>"],
  "ambiguity_score": <float 0.0-1.0>,
  "requires_clarification": <true/false>
}}

Only return the JSON object. No markdown fences."""

        response = await self._adapter.complete({"prompt": prompt})
        raw = response.get("text", "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)

        # Clean up nulls
        constraints = {k: v for k, v in data.get("constraints", {}).items() if v is not None}
        preferences = {k: v for k, v in data.get("preferences", {}).items() if v}

        return UserIntent(
            raw_input=raw_input,
            inferred_domain=data.get("inferred_domain") or domain,
            primary_goal=data.get("primary_goal", raw_input[:100]),
            constraints=constraints,
            preferences=preferences,
            extracted_entities=data.get("extracted_entities", []),
            ambiguity_score=float(data.get("ambiguity_score", 0.0)),
            requires_clarification=bool(data.get("requires_clarification", False)),
            confidence=confidence,
        )

    # ── Deterministic path ────────────────────────────────────────────

    def _deterministic_interpret(
        self, raw_input: str, domain: str | None, confidence: float
    ) -> UserIntent:
        constraints: dict[str, Any] = {}
        budget = _extract_budget(raw_input)
        if budget:
            constraints["budget_inr"] = budget
        nights = _extract_nights(raw_input)
        if nights:
            constraints["nights"] = nights

        preferences = _extract_preferences(raw_input)
        entities = _extract_cities(raw_input)
        goal = _infer_goal(raw_input, domain)
        ambiguity = _compute_ambiguity(raw_input, domain, constraints, entities)

        return UserIntent(
            raw_input=raw_input,
            inferred_domain=domain,
            primary_goal=goal,
            constraints=constraints,
            preferences=preferences,
            extracted_entities=entities,
            ambiguity_score=ambiguity,
            requires_clarification=ambiguity > 0.5,
            confidence=confidence,
        )
