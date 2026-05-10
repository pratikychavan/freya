"""freya/experience/narrative.py

Generates human-readable narrative summaries of completed workflows.

Two modes:
  1. LLM-powered — sends structured context to an LLM adapter for a
     polished natural language summary (used when an adapter is provided).
  2. Deterministic fallback — builds a clean summary from structured
     result data without any LLM call.

Neither mode exposes raw traces, strategies, contracts, or governance
internals. The output is product-facing, not engineering-facing.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from freya.experience.models import NarrativeSummary

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Human labels for completed task IDs
# ---------------------------------------------------------------------------

TASK_LABELS: dict[str, str] = {
    "search_primary_flights":     "Flights searched via primary provider",
    "search_alternative_flights": "Flights found via alternate provider (recovery)",
    "search_hotels":              "Hotels identified near meeting venue",
    "compare_hotels":             "Best hotel selected using deep reasoning",
    "build_itinerary":            "Meeting itinerary built",
    "estimate_costs":             "Total trip costs calculated",
}


class NarrativeSummaryGenerator:
    """Generates human-readable NarrativeSummary objects.

    Parameters
    ----------
    llm_adapter : optional
        Any object implementing ``async complete(request: dict) -> dict``.
        When provided, used for LLM-powered summaries.
        When None, falls back to deterministic rendering.
    """

    def __init__(self, llm_adapter: object | None = None) -> None:
        self._adapter = llm_adapter

    async def generate(
        self,
        goal: str,
        completed_tasks: list[str],
        task_results: dict[str, Any],
        had_recovery: bool = False,
        had_approval: bool = False,
        economics: object | None = None,
    ) -> NarrativeSummary:
        """Generate and return a NarrativeSummary."""
        structured = self._build_structured_context(
            goal, completed_tasks, task_results,
            had_recovery, had_approval, economics,
        )

        if self._adapter is not None:
            try:
                return await self._llm_summary(goal, structured)
            except Exception as exc:
                logger.warning("LLM narrative generation failed (%s) — using fallback.", exc)

        return self._deterministic_summary(goal, structured)

    # ── Private helpers ──────────────────────────────────────────────────

    def _build_structured_context(
        self,
        goal: str,
        completed_tasks: list[str],
        task_results: dict[str, Any],
        had_recovery: bool,
        had_approval: bool,
        economics: object | None,
    ) -> dict[str, Any]:
        ctx: dict[str, Any] = {"goal": goal, "adaptations": []}

        # Flight
        for key in ("search_primary_flights", "search_alternative_flights"):
            r = task_results.get(key, {})
            flights = (r.get("output") or {}).get("flights", [])
            if flights:
                best = min(flights, key=lambda f: f.get("price_inr", 999_999))
                ctx["flight"] = {
                    "airline": best.get("airline"),
                    "flight_number": best.get("flight_number"),
                    "price_inr": best.get("price_inr"),
                    "departure": best.get("departure"),
                    "arrival": best.get("arrival"),
                }
                if key == "search_alternative_flights":
                    ctx["adaptations"].append(
                        "Recovered from primary flight provider outage using an alternate source."
                    )
                break

        # Hotel
        hotel_r = task_results.get("compare_hotels", {})
        hotel_out = (hotel_r.get("output") or {})
        hotel = hotel_out.get("selected_hotel", {})
        if hotel:
            ctx["hotel"] = {
                "name": hotel.get("name"),
                "location": hotel.get("location"),
                "price_per_night_inr": hotel.get("price_per_night_inr"),
                "stars": hotel.get("stars"),
                "distance_from_venue_km": hotel.get("distance_from_venue_km"),
                "reasoning": hotel_out.get("reasoning", ""),
            }
            if hotel_out.get("over_budget"):
                ctx["adaptations"].append(
                    "Hotel selection exceeded preferred budget and required approval — "
                    "approved due to superior proximity to meeting venue."
                )

        # Costs
        cost_r = task_results.get("estimate_costs", {})
        cost_out = (cost_r.get("output") or {})
        if cost_out:
            ctx["costs"] = {
                "flight_inr": cost_out.get("flight_cost_inr"),
                "hotel_inr":  cost_out.get("hotel_cost_inr"),
                "misc_inr":   cost_out.get("misc_cost_inr"),
                "total_inr":  cost_out.get("total_cost_inr"),
                "budget_inr": cost_out.get("budget_inr"),
                "within":     cost_out.get("within_budget"),
            }

        # Adaptations
        if had_recovery and not any("flight provider" in a for a in ctx["adaptations"]):
            ctx["adaptations"].append("System automatically recovered from a temporary service issue.")
        if had_approval and not any("approval" in a for a in ctx["adaptations"]):
            ctx["adaptations"].append("A governance approval was obtained before proceeding.")

        # Economics summary (power detail — not shown in user narrative)
        if economics is not None and hasattr(economics, "current_cost"):
            cost = economics.current_cost()
            ctx["economics"] = {
                "cognitive_invocations": cost.cognitive_invocations,
                "recovery_attempts":     cost.recovery_attempts,
                "estimated_cost_usd":    cost.estimated_monetary_cost,
            }

        return ctx

    async def _llm_summary(self, goal: str, context: dict[str, Any]) -> NarrativeSummary:
        prompt = f"""You are a helpful travel coordination assistant.

A workflow was just completed for the following goal:
"{goal}"

Here is the structured outcome:
{json.dumps(context, indent=2, default=str)}

Write a concise, friendly summary (3-5 sentences) that:
- Confirms the trip was successfully planned
- Mentions the flight and hotel chosen
- Notes any adaptations (recovery, approval) in plain English
- States the total cost
- Does NOT mention technical terms like "workflow", "strategy", "governance", "DAG"

Then list 3-5 key highlights as bullet points.

Return a JSON object:
{{
  "summary": "<paragraph>",
  "highlights": ["<bullet 1>", "<bullet 2>", ...]
}}
Only return the JSON, no markdown fences."""

        response = await self._adapter.complete({"prompt": prompt})
        raw = response.get("text", "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return NarrativeSummary(
            title="Your Trip Plan — Summary",
            summary=data.get("summary", ""),
            highlights=data.get("highlights", []),
        )

    def _deterministic_summary(self, goal: str, context: dict[str, Any]) -> NarrativeSummary:
        parts: list[str] = ["Your business trip to Bangalore has been successfully planned."]

        flight = context.get("flight")
        hotel = context.get("hotel")
        costs = context.get("costs")

        if flight:
            parts.append(
                f"{flight['airline']} flight {flight['flight_number']} "
                f"(₹{flight['price_inr']:,}) departs {flight['departure']}."
            )
        if hotel:
            parts.append(
                f"Staying at {hotel['name']} — {hotel['distance_from_venue_km']} km from venue "
                f"at ₹{hotel['price_per_night_inr']:,}/night."
            )
        if costs and costs.get("total_inr"):
            budget_note = "within budget" if costs.get("within") else "over preferred budget (approved)"
            parts.append(f"Total estimated cost: ₹{costs['total_inr']:,} — {budget_note}.")

        summary = " ".join(parts)

        highlights: list[str] = []
        if flight:
            highlights.append(f"Flight: {flight['airline']} {flight['flight_number']} — ₹{flight['price_inr']:,}")
        if hotel:
            highlights.append(
                f"Hotel: {hotel['name']}, {hotel['stars']}★ — "
                f"₹{hotel['price_per_night_inr']:,}/night, {hotel['distance_from_venue_km']} km from venue"
            )
        if costs:
            highlights.append(f"Total cost: ₹{costs.get('total_inr', 0):,}")
        for adaptation in context.get("adaptations", []):
            highlights.append(adaptation)

        return NarrativeSummary(
            title="Your Trip Plan — Summary",
            summary=summary,
            highlights=highlights,
        )
