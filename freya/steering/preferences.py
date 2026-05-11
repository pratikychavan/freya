"""freya/steering/preferences.py

PreferenceMemory — lightweight, deterministic preference tracking.

Stores and retrieves user operational preferences from an in-memory
dictionary backed by an optional JSON file on disk.

NO vector databases, NO embeddings, NO ML models.
Preference inference is purely statistical — count-based with recency
weighting.

Stored preference names (examples):
  cost_sensitivity      → "high" | "low"
  convenience           → "preferred" | "not_preferred"
  speed                 → "preferred" | "not_preferred"
  hotel_proximity       → "preferred" | "not_preferred"
  premium               → "preferred" | "not_preferred"
  approval_tolerance    → "low" | "medium" | "high"
"""
from __future__ import annotations

import json
import logging
import os
from collections import Counter, defaultdict
from typing import Any

from freya.steering.models import OperationalPreference, SteeringDecision

logger = logging.getLogger(__name__)

_DEFAULT_PATH = os.path.join(
    os.path.expanduser("~"), ".freya", "preference_memory.json"
)

# How many past decisions to consider "recent" for confidence weighting
_RECENCY_WINDOW = 10
# Minimum number of observations before we claim a preference with confidence
_MIN_OBSERVATIONS = 2


class PreferenceMemory:
    """Remember and infer user operational preferences from past decisions.

    Parameters
    ----------
    persist_path : str | None
        Path to a JSON file for lightweight persistence.
        Pass ``None`` to keep everything in-memory only.
    """

    def __init__(self, persist_path: str | None = _DEFAULT_PATH) -> None:
        self._path = persist_path
        # {preference_name: [(value, weight)]}  — weight=1.0 for old, 1.5 for recent
        self._history: dict[str, list[tuple[str, float]]] = defaultdict(list)
        self._explicit: dict[str, OperationalPreference] = {}  # user-stated prefs
        if persist_path:
            self._load()

    # ── Recording ─────────────────────────────────────────────────────

    def record_decision(self, decision: SteeringDecision) -> None:
        """Infer preferences from a steering decision and record them."""
        option = decision.chosen_option_id
        updates = decision.applied_updates

        # Map known option IDs / update keys to preference signals
        signals: list[tuple[str, str]] = []

        if option in ("economy_flight", "reduce_hotel_quality", "stay_farther", "cost_wins"):
            signals.append(("cost_sensitivity", "high"))
        if option in ("increase_budget", "premium_only_return", "increase_flight_budget"):
            signals.append(("cost_sensitivity", "low"))
        if option in ("proximity_wins", "increase_budget"):
            signals.append(("hotel_proximity", "preferred"))
        if option == "stay_farther":
            signals.append(("hotel_proximity", "not_preferred"))
        if option == "use_deterministic":
            signals.append(("speed", "preferred"))
        if option == "keep_cognitive":
            signals.append(("quality", "preferred"))
        if "priority" in updates:
            p = updates["priority"]
            if p == "cost":
                signals.append(("cost_sensitivity", "high"))
            elif p == "speed":
                signals.append(("speed", "preferred"))
            elif p == "quality":
                signals.append(("quality", "preferred"))

        for name, value in signals:
            self._history[name].append((value, 1.5))   # recent = higher weight
            # Downweight older entries
            if len(self._history[name]) > _RECENCY_WINDOW:
                old = self._history[name][0]
                self._history[name][0] = (old[0], max(0.5, old[1] - 0.1))

        if self._path:
            self._save()

    def record_explicit(self, name: str, value: str, confidence: float = 1.0) -> None:
        """Record a preference explicitly stated by the user."""
        self._explicit[name] = OperationalPreference(
            preference_name=name, preference_value=value, confidence=confidence
        )
        if self._path:
            self._save()

    # ── Retrieval ─────────────────────────────────────────────────────

    def get(self, name: str) -> OperationalPreference | None:
        """Return the best-guess preference for *name*, or None."""
        # Explicit always wins
        if name in self._explicit:
            return self._explicit[name]
        return self._infer(name)

    def all_preferences(self) -> list[OperationalPreference]:
        """Return all known preferences (explicit + inferred)."""
        seen: set[str] = set()
        result: list[OperationalPreference] = []

        for name in list(self._explicit) + list(self._history):
            if name in seen:
                continue
            seen.add(name)
            pref = self.get(name)
            if pref:
                result.append(pref)

        return result

    def tendency_summary(self) -> dict[str, str]:
        """Return a human-readable dict of known tendencies."""
        out: dict[str, str] = {}
        for pref in self.all_preferences():
            out[pref.preference_name.replace("_", " ").title()] = (
                f"{pref.preference_value}  (confidence {pref.confidence:.0%})"
            )
        return out

    # ── Persistence ───────────────────────────────────────────────────

    def _save(self) -> None:
        if not self._path:
            return
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            payload: dict[str, Any] = {
                "history": {k: v for k, v in self._history.items()},
                "explicit": {
                    k: p.model_dump() for k, p in self._explicit.items()
                },
            }
            with open(self._path, "w") as f:
                json.dump(payload, f, indent=2)
        except OSError as exc:
            logger.warning("PreferenceMemory: could not save to %s: %s", self._path, exc)

    def _load(self) -> None:
        if not self._path or not os.path.exists(self._path):
            return
        try:
            with open(self._path) as f:
                payload = json.load(f)
            for name, entries in payload.get("history", {}).items():
                self._history[name] = [tuple(e) for e in entries]  # type: ignore[misc]
            for name, raw in payload.get("explicit", {}).items():
                self._explicit[name] = OperationalPreference(**raw)
        except (OSError, json.JSONDecodeError, Exception) as exc:
            logger.warning("PreferenceMemory: could not load from %s: %s", self._path, exc)

    # ── Inference ─────────────────────────────────────────────────────

    def _infer(self, name: str) -> OperationalPreference | None:
        entries = self._history.get(name, [])
        if len(entries) < _MIN_OBSERVATIONS:
            return None

        weighted: dict[str, float] = defaultdict(float)
        for value, weight in entries:
            weighted[value] += weight

        total = sum(weighted.values())
        best_value = max(weighted, key=lambda k: weighted[k])
        confidence = min(weighted[best_value] / total, 0.95)

        return OperationalPreference(
            preference_name=name,
            preference_value=best_value,
            confidence=confidence,
        )
