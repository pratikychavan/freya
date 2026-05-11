"""freya/intent/classifier.py

Intent domain classification.

Maps a natural-language input to a known workflow domain using a
keyword-signal scoring approach (deterministic) with an optional LLM
path for ambiguous inputs.

Supported domains match TEMPLATE_REGISTRY in templates.py.
"""
from __future__ import annotations

import re

from freya.intent.templates import TEMPLATE_REGISTRY, WorkflowTemplate

# ---------------------------------------------------------------------------
# Keyword signal tables — domain → (keywords, weight)
# Higher weight = stronger signal
# ---------------------------------------------------------------------------

_DOMAIN_SIGNALS: dict[str, list[tuple[list[str], float]]] = {
    "business_travel": [
        (["trip", "travel", "flight", "hotel", "itinerary", "bangalore", "mumbai",
          "delhi", "airport", "book.*ticket", "fly", "airline"], 3.0),
        (["business", "client", "meeting", "venue", "office"], 1.5),
        (["budget", "cost", "₹", "inr", "nights?", "days?"], 1.0),
    ],
    "incident_response": [
        (["incident", "outage", "down", "failure", "alert", "p0", "p1", "crisis",
          "broken", "error", "sev[0-9]"], 3.0),
        (["diagnose", "triage", "escalat", "resolve", "remediat", "post.?mortem"], 2.0),
        (["monitor", "system", "service", "infrastructure", "ops"], 1.0),
    ],
    "data_pipeline": [
        (["data", "pipeline", "etl", "ingest", "transform", "load", "dataset",
          "extract", "migrate", "sync"], 3.0),
        (["schema", "validate", "quality", "source", "destination", "warehouse"], 2.0),
        (["csv", "json", "parquet", "s3", "bigquery", "postgres", "mysql"], 1.5),
    ],
    "scheduling": [
        (["schedul", "calendar", "availab", "meeting", "slot", "book.*room",
          "appointment", "invite"], 3.0),
        (["attendee", "participant", "room", "resource", "venue", "agenda"], 2.0),
        (["time", "date", "when", "hour", "duration"], 0.5),
    ],
    "procurement": [
        (["procure", "purchase", "buy", "order", "vendor", "supplier", "quote",
          "sourcing", "rfq", "invoice"], 3.0),
        (["approval", "budget", "spend", "cost", "price", "quantity"], 1.5),
        (["delivery", "track", "ship", "item", "product", "goods"], 1.0),
    ],
}


class IntentClassifier:
    """Classifies a user input into a known operational domain.

    Uses weighted keyword scoring. Returns None if no domain scores above
    the minimum confidence threshold (meaning the synthesizer will return
    a generic blueprint or ask for clarification).
    """

    MIN_CONFIDENCE: float = 1.5   # minimum score to claim a domain
    AMBIGUITY_MARGIN: float = 0.6  # if top-2 scores within this ratio, flag as ambiguous

    def classify(self, text: str) -> tuple[str | None, float]:
        """Return (domain_id, confidence_score). domain_id is None if unclear."""
        text_lower = text.lower()
        scores: dict[str, float] = {}

        for domain, signal_groups in _DOMAIN_SIGNALS.items():
            total = 0.0
            for keywords, weight in signal_groups:
                matched = sum(
                    1 for kw in keywords
                    if re.search(r"\b" + kw + r"\b", text_lower)
                )
                total += matched * weight
            scores[domain] = total

        if not scores or max(scores.values()) < self.MIN_CONFIDENCE:
            return None, 0.0

        sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_domain, top_score = sorted_domains[0]

        # Normalise confidence to [0, 1]
        confidence = min(top_score / 10.0, 1.0)
        return top_domain, confidence

    def is_ambiguous(self, text: str) -> bool:
        """Return True if two domains are nearly equally matched."""
        text_lower = text.lower()
        scores: dict[str, float] = {}
        for domain, signal_groups in _DOMAIN_SIGNALS.items():
            total = 0.0
            for keywords, weight in signal_groups:
                matched = sum(1 for kw in keywords if re.search(r"\b" + kw + r"\b", text_lower))
                total += matched * weight
            scores[domain] = total

        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) < 2 or sorted_scores[0] < self.MIN_CONFIDENCE:
            return False
        return (sorted_scores[0] - sorted_scores[1]) < self.AMBIGUITY_MARGIN

    def get_template(self, domain: str | None) -> WorkflowTemplate | None:
        if domain is None:
            return None
        return TEMPLATE_REGISTRY.get(domain)
