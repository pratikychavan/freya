"""Travel tools for the Business Travel coordinator demo.

All tools operate on static local datasets — no external APIs.
"""
from __future__ import annotations

import json
import logging
from typing import ClassVar, Type, TYPE_CHECKING

from pydantic import BaseModel

from freya.tool import Tool
from freya.demo.datasets import (
    FLIGHTS_PRIMARY,
    FLIGHTS_ALTERNATE,
    HOTELS,
    MEETING_VENUE,
    MEETING_AGENDA,
    MISC_COSTS,
    TOTAL_TRIP_BUDGET_INR,
)

if TYPE_CHECKING:
    from freya.context import ExecutionContext

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# SearchPrimaryFlightsTool
# Simulates a provider outage on the first call.
# ═══════════════════════════════════════════════════════════════════════

class FlightSearchInput(BaseModel):
    origin: str = "Pune"
    destination: str = "Bangalore"
    date: str = "next_monday"


class FlightSearchOutput(BaseModel):
    flights: list[dict]
    source: str
    count: int


class SearchPrimaryFlightsTool(Tool):
    """Search primary flight provider for Pune → Bangalore."""

    name: ClassVar[str] = "search_primary_flights"
    input_model: ClassVar[Type[BaseModel]] = FlightSearchInput
    output_model: ClassVar[Type[BaseModel]] = FlightSearchOutput

    def __init__(self) -> None:
        self._call_count = 0

    async def execute(self, input: FlightSearchInput, context: "ExecutionContext") -> FlightSearchOutput:
        self._call_count += 1
        if self._call_count == 1:
            # Simulate provider outage on first call
            raise RuntimeError(
                "Primary flight provider temporarily unavailable (HTTP 503). "
                "Retry or switch to alternate provider."
            )
        # Second+ call succeeds (not normally reached since recovery uses alternate tool)
        return FlightSearchOutput(
            flights=FLIGHTS_PRIMARY,
            source="primary",
            count=len(FLIGHTS_PRIMARY),
        )


# ═══════════════════════════════════════════════════════════════════════
# SearchAlternativeFlightsTool
# Always succeeds — used after primary provider fails.
# ═══════════════════════════════════════════════════════════════════════

class SearchAlternativeFlightsTool(Tool):
    """Search alternate flight provider — fallback when primary is unavailable."""

    name: ClassVar[str] = "search_alternative_flights"
    input_model: ClassVar[Type[BaseModel]] = FlightSearchInput
    output_model: ClassVar[Type[BaseModel]] = FlightSearchOutput

    async def execute(self, input: FlightSearchInput, context: "ExecutionContext") -> FlightSearchOutput:
        return FlightSearchOutput(
            flights=FLIGHTS_ALTERNATE,
            source="alternate",
            count=len(FLIGHTS_ALTERNATE),
        )


# ═══════════════════════════════════════════════════════════════════════
# SearchHotelsTool
# Returns the curated hotel dataset with deliberately ambiguous candidates.
# ═══════════════════════════════════════════════════════════════════════

class HotelSearchInput(BaseModel):
    destination: str = "Bangalore"
    check_in: str = "next_monday"
    nights: int = 2
    max_candidates: int = 10


class HotelSearchOutput(BaseModel):
    hotels: list[dict]
    count: int
    venue_name: str
    venue_location: str


class SearchHotelsTool(Tool):
    """Search hotels near the meeting venue in Bangalore."""

    name: ClassVar[str] = "search_hotels"
    input_model: ClassVar[Type[BaseModel]] = HotelSearchInput
    output_model: ClassVar[Type[BaseModel]] = HotelSearchOutput

    async def execute(self, input: HotelSearchInput, context: "ExecutionContext") -> HotelSearchOutput:
        hotels = HOTELS[: input.max_candidates]
        return HotelSearchOutput(
            hotels=hotels,
            count=len(hotels),
            venue_name=MEETING_VENUE["name"],
            venue_location=MEETING_VENUE["location"],
        )


# ═══════════════════════════════════════════════════════════════════════
# CompareHotelsTool
# Uses real OpenRouter LLM reasoning (cognitive model).
# ═══════════════════════════════════════════════════════════════════════

class HotelCompareInput(BaseModel):
    hotels: list[dict]
    venue_name: str
    venue_location: str
    budget_per_night_inr: int
    nights: int
    trip_context: str = ""


class HotelCompareOutput(BaseModel):
    selected_hotel: dict
    selected_hotel_id: str
    reasoning: str
    total_hotel_cost_inr: int
    over_budget: bool
    alternatives_considered: list[str]


class CompareHotelsTool(Tool):
    """Compare hotel options using real LLM reasoning (cognitive strategy).

    Calls OpenRouter with the configured cognitive model to reason about
    the best hotel choice given budget, convenience, and meeting suitability.
    """

    name: ClassVar[str] = "compare_hotels"
    input_model: ClassVar[Type[BaseModel]] = HotelCompareInput
    output_model: ClassVar[Type[BaseModel]] = HotelCompareOutput

    def __init__(self, cognitive_adapter: object) -> None:
        self._adapter = cognitive_adapter

    async def execute(self, input: HotelCompareInput, context: "ExecutionContext") -> HotelCompareOutput:
        # Format hotel list for the prompt
        hotel_lines = []
        for h in input.hotels:
            hotel_lines.append(
                f"- {h['id']}: {h['name']} | {h['location']} | "
                f"₹{h['price_per_night_inr']:,}/night | {h['stars']}★ | "
                f"{h['distance_from_venue_km']}km from venue "
                f"({h['travel_time_to_venue_mins']} min travel) | "
                f"Notes: {h['notes']}"
            )
        hotels_block = "\n".join(hotel_lines)

        total_budget = input.budget_per_night_inr * input.nights
        prompt = f"""You are a corporate travel advisor optimizing a business trip to Bangalore.

MEETING VENUE: {input.venue_name}, {input.venue_location}
TRIP DURATION: {input.nights} nights
PREFERRED HOTEL BUDGET: ₹{input.budget_per_night_inr:,}/night (₹{total_budget:,} total for {input.nights} nights)
{('CONTEXT: ' + input.trip_context) if input.trip_context else ''}

HOTEL OPTIONS:
{hotels_block}

Your task: recommend the BEST hotel for this business trip.

Optimize for:
1. Proximity to the meeting venue (minimize commute stress for client meetings)
2. Business suitability (meeting rooms, reliable wifi, professional environment)
3. Cost efficiency (stay within budget when possible, but proximity matters for client work)
4. Overall trip productivity

Return your recommendation as a JSON object (and ONLY the JSON object, no other text):
{{
  "selected_hotel_id": "<hotel id>",
  "reasoning": "<2-3 sentence explanation of why this hotel was chosen>",
  "alternatives_considered": ["<hotel name 1>", "<hotel name 2>"]
}}
"""

        response = await self._adapter.complete({
            "prompt": prompt,
            "system": (
                "You are an expert corporate travel advisor. "
                "You return only valid JSON without any markdown fences or extra text."
            ),
        })

        raw = response.get("text", "").strip()
        logger.debug("CompareHotels LLM response: %s", raw[:400])

        # Parse LLM response
        try:
            # Strip any markdown fences the model might add
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
        except Exception as exc:
            # Fallback: pick the hotel closest to venue within budget
            logger.warning("CompareHotels JSON parse failed: %s — using fallback", exc)
            within_budget = [
                h for h in input.hotels
                if h["price_per_night_inr"] <= input.budget_per_night_inr
            ]
            candidates = within_budget or input.hotels
            best = min(candidates, key=lambda h: h["distance_from_venue_km"])
            data = {
                "selected_hotel_id": best["id"],
                "reasoning": f"Selected {best['name']} as closest within budget (fallback selection).",
                "alternatives_considered": [h["name"] for h in candidates if h["id"] != best["id"]],
            }

        selected_id = data.get("selected_hotel_id", "")
        selected = next((h for h in input.hotels if h["id"] == selected_id), input.hotels[0])
        total_cost = selected["price_per_night_inr"] * input.nights

        return HotelCompareOutput(
            selected_hotel=selected,
            selected_hotel_id=selected_id,
            reasoning=data.get("reasoning", ""),
            total_hotel_cost_inr=total_cost,
            over_budget=selected["price_per_night_inr"] > input.budget_per_night_inr,
            alternatives_considered=data.get("alternatives_considered", []),
        )


# ═══════════════════════════════════════════════════════════════════════
# BuildItineraryTool — deterministic
# ═══════════════════════════════════════════════════════════════════════

class ItineraryInput(BaseModel):
    venue_name: str = ""
    venue_location: str = ""
    nights: int = 2


class ItineraryOutput(BaseModel):
    venue: str
    days: dict
    total_meeting_days: int


class BuildItineraryTool(Tool):
    """Build the meeting itinerary from the static agenda template."""

    name: ClassVar[str] = "build_itinerary"
    input_model: ClassVar[Type[BaseModel]] = ItineraryInput
    output_model: ClassVar[Type[BaseModel]] = ItineraryOutput

    async def execute(self, input: ItineraryInput, context: "ExecutionContext") -> ItineraryOutput:
        venue = input.venue_name or MEETING_VENUE["name"]
        venue_loc = input.venue_location or MEETING_VENUE["location"]
        return ItineraryOutput(
            venue=f"{venue} ({venue_loc})",
            days=MEETING_AGENDA,
            total_meeting_days=len(MEETING_AGENDA),
        )


# ═══════════════════════════════════════════════════════════════════════
# EstimateCostsTool — deterministic
# ═══════════════════════════════════════════════════════════════════════

class CostEstimateInput(BaseModel):
    flight_price_inr: int = 0
    hotel_price_per_night_inr: int = 0
    nights: int = 2
    budget_inr: int = TOTAL_TRIP_BUDGET_INR


class CostEstimateOutput(BaseModel):
    flight_cost_inr: int
    hotel_cost_inr: int
    misc_cost_inr: int
    total_cost_inr: int
    budget_inr: int
    within_budget: bool
    summary: str


class EstimateCostsTool(Tool):
    """Estimate total trip costs and compare against budget."""

    name: ClassVar[str] = "estimate_costs"
    input_model: ClassVar[Type[BaseModel]] = CostEstimateInput
    output_model: ClassVar[Type[BaseModel]] = CostEstimateOutput

    async def execute(self, input: CostEstimateInput, context: "ExecutionContext") -> CostEstimateOutput:
        misc = (
            MISC_COSTS["airport_transfer_inr"] * 2
            + MISC_COSTS["local_transport_inr"] * input.nights
            + MISC_COSTS["meals_per_day_inr"] * input.nights
            + MISC_COSTS["incidentals_inr"] * input.nights
        )
        hotel_total = input.hotel_price_per_night_inr * input.nights
        total = input.flight_price_inr + hotel_total + misc
        within = total <= input.budget_inr

        summary = (
            f"₹{total:,} total for {input.nights}-night trip"
            f" {'(within ₹' + str(input.budget_inr // 1000) + 'k budget)' if within else '(over budget — approved)'}"
        )

        return CostEstimateOutput(
            flight_cost_inr=input.flight_price_inr,
            hotel_cost_inr=hotel_total,
            misc_cost_inr=misc,
            total_cost_inr=total,
            budget_inr=input.budget_inr,
            within_budget=within,
            summary=summary,
        )
