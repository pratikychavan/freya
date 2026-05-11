"""freya/hitl/semantic/extractor.py

OperationalSemanticExtractor — pulls structured operational meaning from
classified guidance text.

Extracts:
  constraints  — budget changes, nights, hotel tier, flight class
  preferences  — proximity, metro, venue, cost sensitivity, speed, quality
  policy deltas — analysis depth, retry count

Goes beyond shallow entity extraction: uses phrase-level co-occurrence
and context-aware patterns to produce workflow-meaningful output.
"""
from __future__ import annotations

import re
from typing import Any


# ── Preference signal tables ──────────────────────────────────────────
_PROXIMITY_SIGNALS = ["near ", "close to", "adjacent to", "walking distance", "next to"]
_METRO_SIGNALS = ["metro", "subway", "transit", "public transport", "tube"]
_VENUE_SIGNALS = ["venue", "office", "client site", "client office", "meeting place"]
_BUDGET_CONSCIOUS = ["cheaper", "affordable", "budget", "economical", "lower cost", "save money"]
_PREMIUM_SIGNALS = ["premium", "luxury", "5 star", "five star", "business class", "first class"]
_SPEED_SIGNALS = ["faster", "quicker", "asap", "urgent", "speed", "quickly"]
_QUALITY_SIGNALS = ["better quality", "best option", "top tier", "highest quality", "best possible"]
_COST_OVER_CONV = ["cost over convenience", "cheaper over convenient", "save over comfort"]
_CONV_OVER_COST = ["convenience over cost", "convenient over cheap", "comfort over cost"]

# Regex patterns for constraint values
_BUDGET_AMOUNT_RE = re.compile(
    r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*([kKlL]?)", re.I
)
_NIGHTS_RE = re.compile(r"(\d+)\s*(?:-\s*)?(?:night|day)s?", re.I)
_PERCENT_RE = re.compile(r"(\d+)\s*%")
_DEPTH_REDUCE_RE = re.compile(
    r"(?:reduce|lower|decrease|cut)\s+(?:reasoning|analysis|cognitive)\s+depth", re.I
)
_RETRIES_RE = re.compile(r"(\d+)\s*(?:retries|retry|attempts?)", re.I)


def _norm(text: str) -> str:
    return text.lower().strip()


def _parse_amount(value: str, unit: str) -> int:
    try:
        num = float(value.replace(",", ""))
        u = unit.strip().lower()
        if u == "k":
            num *= 1_000
        elif u == "l":
            num *= 100_000
        return int(num)
    except ValueError:
        return 0


class OperationalSemanticExtractor:
    """Extract operational constraints and preferences from guidance text."""

    def extract(self, text: str) -> tuple[dict[str, Any], dict[str, Any]]:
        """Return (constraints, preferences) extracted from *text*."""
        n = _norm(text)
        constraints = self._extract_constraints(n, text)
        preferences = self._extract_preferences(n)
        return constraints, preferences

    # ── Constraints ───────────────────────────────────────────────────

    def _extract_constraints(self, n: str, original: str) -> dict[str, Any]:
        c: dict[str, Any] = {}

        # Budget amount
        m = _BUDGET_AMOUNT_RE.search(original)
        if m:
            amount = _parse_amount(m.group(1), m.group(2) if len(m.groups()) > 1 else "")
            if amount:
                # Determine direction
                if any(kw in n for kw in ("reduce", "lower", "cut", "less", "cheaper")):
                    c["budget_delta"] = -amount
                elif any(kw in n for kw in ("increase", "raise", "more", "higher")):
                    c["budget_delta"] = +amount
                else:
                    c["budget_inr"] = amount

        # Nights
        m2 = _NIGHTS_RE.search(original)
        if m2:
            c["nights"] = int(m2.group(1))

        # Percentage reduction
        if "%" in n:
            pm = _PERCENT_RE.search(n)
            if pm:
                pct = int(pm.group(1))
                if any(kw in n for kw in ("reduce", "cut", "lower", "less")):
                    c["reduction_percent"] = pct

        # Analysis depth reduction
        if _DEPTH_REDUCE_RE.search(original):
            c["analysis_depth"] = "reduced"

        # Retry count
        rm = _RETRIES_RE.search(n)
        if rm:
            c["max_retries"] = int(rm.group(1))
        elif any(kw in n for kw in ("fewer retries", "fail fast", "stop retrying")):
            c["max_retries"] = 2

        return c

    # ── Preferences ───────────────────────────────────────────────────

    def _extract_preferences(self, n: str) -> dict[str, Any]:
        p: dict[str, Any] = {}

        if any(s in n for s in _PROXIMITY_SIGNALS):
            p["hotel_proximity"] = True
        if any(s in n for s in _METRO_SIGNALS):
            p["metro_access"] = True
        if any(s in n for s in _VENUE_SIGNALS):
            p["near_venue"] = True
        if any(s in n for s in _BUDGET_CONSCIOUS):
            p["cost_sensitivity"] = "high"
        if any(s in n for s in _PREMIUM_SIGNALS):
            p["premium"] = True
        if any(s in n for s in _SPEED_SIGNALS):
            p["speed"] = "preferred"
        if any(s in n for s in _QUALITY_SIGNALS):
            p["quality"] = "preferred"
        if any(s in n for s in _COST_OVER_CONV):
            p["priority_order"] = "cost_over_convenience"
        if any(s in n for s in _CONV_OVER_COST):
            p["priority_order"] = "convenience_over_cost"

        return p
