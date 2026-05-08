"""Model routing configuration for the Business Travel demo.

Different execution strategies use different OpenRouter models to demonstrate
cost-aware adaptive execution.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Primary model routing table
# ---------------------------------------------------------------------------
MODEL_ROUTING: dict[str, str] = {
    # Cheap, fast — used for deterministic structured tasks (flight/hotel lookup)
    "deterministic": "mistralai/mistral-7b-instruct:free",
    # Stronger reasoning — used for ambiguous/cognitive tasks (hotel comparison)
    "cognitive": "anthropic/claude-3-haiku",
    # Medium — used for recovery planning
    "recovery": "openai/gpt-4o-mini",
    # Cheap summarisation
    "summarization": "openai/gpt-4o-mini",
}

# Timeouts (seconds)
TIMEOUT_SECONDS: dict[str, float] = {
    "deterministic": 20.0,
    "cognitive": 45.0,
    "recovery": 25.0,
    "summarization": 15.0,
}

# Cost-per-1k-token estimates (USD) — for economics tracking
TOKEN_COST_USD_PER_1K: dict[str, float] = {
    "deterministic": 0.0,        # free tier
    "cognitive": 0.00025,        # claude-3-haiku input pricing
    "recovery": 0.00015,
    "summarization": 0.00015,
}
