"""TravelPlanner — state-machine planner for the Business Travel demo.

Uses the Freya BasePlanner interface. Each call to plan_next() returns
the next DAG task based on what has already been completed.

The planner sets context.planning_mode to signal cognitive vs deterministic
to the strategy engine — no random behaviour, fully inspectable.

plan_recovery() handles the simulated flight provider failure.
"""
from __future__ import annotations

import logging
from typing import Any

from freya.dag.models import DAG, DAGTask
from freya.planner.base import BasePlanner
from freya.planner.context import PlanningContext
from freya.planner.mode import PlanningMode
from freya.demo.datasets import (
    PREFERRED_HOTEL_BUDGET_PER_NIGHT_INR,
    MEETING_VENUE,
    TRIP_NIGHTS,
)

logger = logging.getLogger(__name__)


class TravelPlanner(BasePlanner):
    """State-machine planner for the Business Travel Coordinator demo.

    Workflow stages (in order):
      1. search_primary_flights  — may fail (simulated provider outage)
      2. search_hotels           — deterministic, returns candidates
      3. compare_hotels          — COGNITIVE: real LLM reasoning
      4. build_itinerary         — deterministic
      5. estimate_costs          — deterministic
      6. done                    — empty DAG returned

    Recovery:
      If search_primary_flights fails, plan_recovery() returns
      search_alternative_flights (alternate provider).
    """

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _flights_done(context: PlanningContext) -> bool:
        completed = set(context.completed_tasks)
        return (
            "search_primary_flights" in completed
            or "search_alternative_flights" in completed
        )

    @staticmethod
    def _best_flight(context: PlanningContext) -> dict:
        """Pick the cheapest flight from whichever source succeeded."""
        for key in ("search_primary_flights", "search_alternative_flights"):
            result = context.task_results.get(key, {})
            output = (result.get("output") or {})
            flights = output.get("flights", [])
            if flights:
                return min(flights, key=lambda f: f.get("price_inr", 999_999))
        return {}

    @staticmethod
    def _hotel_candidates(context: PlanningContext) -> list[dict]:
        result = context.task_results.get("search_hotels", {})
        output = (result.get("output") or {})
        return output.get("hotels", [])

    @staticmethod
    def _selected_hotel(context: PlanningContext) -> dict:
        result = context.task_results.get("compare_hotels", {})
        output = (result.get("output") or {})
        return output.get("selected_hotel", {})

    # ── BasePlanner interface ────────────────────────────────────────────

    async def plan_next(self, context: PlanningContext) -> DAG:
        completed = set(context.completed_tasks)
        failed = set(context.failed_tasks)

        # ── Stage 1: Search flights ──────────────────────────────────────
        if not self._flights_done(context):
            context.planning_mode = PlanningMode.DETERMINISTIC
            logger.info("TravelPlanner: planning search_primary_flights")
            return DAG(tasks=[DAGTask(
                task_id="search_primary_flights",
                type="tool",
                input={
                    "tool_name": "search_primary_flights",
                    "tool_input": {"origin": "Pune", "destination": "Bangalore", "date": "next_monday"},
                },
            )])

        # ── Stage 2: Search hotels ───────────────────────────────────────
        if "search_hotels" not in completed:
            context.planning_mode = PlanningMode.DETERMINISTIC
            logger.info("TravelPlanner: planning search_hotels")
            return DAG(tasks=[DAGTask(
                task_id="search_hotels",
                type="tool",
                input={
                    "tool_name": "search_hotels",
                    "tool_input": {"destination": "Bangalore", "check_in": "next_monday", "nights": TRIP_NIGHTS},
                },
            )])

        # ── Stage 3: Cognitive hotel comparison ─────────────────────────
        if "compare_hotels" not in completed:
            context.planning_mode = PlanningMode.COGNITIVE  # signal escalation
            hotels = self._hotel_candidates(context)
            logger.info("TravelPlanner: planning compare_hotels (COGNITIVE) — %d candidates", len(hotels))
            return DAG(tasks=[DAGTask(
                task_id="compare_hotels",
                type="tool",
                input={
                    "tool_name": "compare_hotels",
                    "tool_input": {
                        "hotels": hotels,
                        "venue_name": MEETING_VENUE["name"],
                        "venue_location": MEETING_VENUE["location"],
                        "budget_per_night_inr": PREFERRED_HOTEL_BUDGET_PER_NIGHT_INR,
                        "nights": TRIP_NIGHTS,
                        "trip_context": "Business trip with client meetings — proximity is important.",
                    },
                },
            )])

        # ── Stage 4: Build itinerary ─────────────────────────────────────
        if "build_itinerary" not in completed:
            context.planning_mode = PlanningMode.DETERMINISTIC
            logger.info("TravelPlanner: planning build_itinerary")
            return DAG(tasks=[DAGTask(
                task_id="build_itinerary",
                type="tool",
                input={
                    "tool_name": "build_itinerary",
                    "tool_input": {
                        "venue_name": MEETING_VENUE["name"],
                        "venue_location": MEETING_VENUE["location"],
                        "nights": TRIP_NIGHTS,
                    },
                },
            )])

        # ── Stage 5: Estimate costs ──────────────────────────────────────
        if "estimate_costs" not in completed:
            context.planning_mode = PlanningMode.DETERMINISTIC
            flight = self._best_flight(context)
            hotel = self._selected_hotel(context)
            logger.info("TravelPlanner: planning estimate_costs")
            return DAG(tasks=[DAGTask(
                task_id="estimate_costs",
                type="tool",
                input={
                    "tool_name": "estimate_costs",
                    "tool_input": {
                        "flight_price_inr": flight.get("price_inr", 0),
                        "hotel_price_per_night_inr": hotel.get("price_per_night_inr", 0),
                        "nights": TRIP_NIGHTS,
                        "budget_inr": 40_000,
                    },
                },
            )])

        # ── Done ─────────────────────────────────────────────────────────
        logger.info("TravelPlanner: all stages complete — returning empty DAG")
        context.planning_mode = PlanningMode.DETERMINISTIC
        return DAG(tasks=[])

    async def plan_recovery(
        self, context: PlanningContext, failed_observations: list[Any]
    ) -> DAG:
        """Recovery plan when search_primary_flights fails."""
        failed_ids = [getattr(o, "task_id", "") for o in failed_observations]
        if "search_primary_flights" in failed_ids:
            logger.info("TravelPlanner: recovery — switching to alternate flight provider")
            context.planning_mode = PlanningMode.DETERMINISTIC
            return DAG(tasks=[DAGTask(
                task_id="search_alternative_flights",
                type="tool",
                input={
                    "tool_name": "search_alternative_flights",
                    "tool_input": {"origin": "Pune", "destination": "Bangalore", "date": "next_monday"},
                },
            )])
        # No known recovery for other failures
        return DAG(tasks=[])
