"""Static curated datasets for the Business Travel demo.

All data is local and deterministic — no external APIs.
Designed to exercise all Freya features:
  - flight search failure + recovery (primary provider fails)
  - cognitive hotel comparison (ambiguous candidates)
  - governance approval (Taj > preferred hotel budget)
  - cost estimation and economics tracking
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Budget parameters
# ---------------------------------------------------------------------------
TOTAL_TRIP_BUDGET_INR: int = 40_000
PREFERRED_HOTEL_BUDGET_PER_NIGHT_INR: int = 10_000  # ₹20k for 2 nights (preferred limit); Taj ₹18k exceeds by ₹8k
TRIP_NIGHTS: int = 2

# ---------------------------------------------------------------------------
# Flights — primary provider (will fail first call to simulate provider outage)
# ---------------------------------------------------------------------------
FLIGHTS_PRIMARY: list[dict] = [
    {
        "id": "F1",
        "airline": "IndiGo",
        "flight_number": "6E-214",
        "origin": "Pune (PNQ)",
        "destination": "Bangalore (BLR)",
        "departure": "Mon 07:00",
        "arrival": "Mon 08:30",
        "duration_mins": 90,
        "price_inr": 9_500,
        "class": "Economy",
        "seats_available": 12,
    },
    {
        "id": "F2",
        "airline": "Air India",
        "flight_number": "AI-503",
        "origin": "Pune (PNQ)",
        "destination": "Bangalore (BLR)",
        "departure": "Mon 10:00",
        "arrival": "Mon 11:30",
        "duration_mins": 90,
        "price_inr": 11_200,
        "class": "Economy",
        "seats_available": 6,
    },
    {
        "id": "F3",
        "airline": "Vistara",
        "flight_number": "UK-851",
        "origin": "Pune (PNQ)",
        "destination": "Bangalore (BLR)",
        "departure": "Mon 14:00",
        "arrival": "Mon 15:15",
        "duration_mins": 75,
        "price_inr": 13_800,
        "class": "Economy",
        "seats_available": 4,
    },
]

# ---------------------------------------------------------------------------
# Flights — alternate provider (used when primary fails)
# ---------------------------------------------------------------------------
FLIGHTS_ALTERNATE: list[dict] = [
    {
        "id": "AF1",
        "airline": "SpiceJet",
        "flight_number": "SG-312",
        "origin": "Pune (PNQ)",
        "destination": "Bangalore (BLR)",
        "departure": "Mon 06:30",
        "arrival": "Mon 08:00",
        "duration_mins": 90,
        "price_inr": 8_900,
        "class": "Economy",
        "seats_available": 18,
    },
    {
        "id": "AF2",
        "airline": "GoFirst",
        "flight_number": "G8-189",
        "origin": "Pune (PNQ)",
        "destination": "Bangalore (BLR)",
        "departure": "Mon 11:30",
        "arrival": "Mon 13:00",
        "duration_mins": 90,
        "price_inr": 10_200,
        "class": "Economy",
        "seats_available": 9,
    },
]

# ---------------------------------------------------------------------------
# Hotels — deliberately ambiguous to trigger cognitive escalation
# H1 and H5 are close in price but different distance.
# H4 (Taj) is premium, closest, and over-budget → triggers governance.
# ---------------------------------------------------------------------------
HOTELS: list[dict] = [
    {
        "id": "H1",
        "name": "Lemon Tree Hotel Whitefield",
        "location": "Whitefield",
        "price_per_night_inr": 8_500,
        "stars": 4,
        "distance_from_venue_km": 16.2,
        "travel_time_to_venue_mins": 55,
        "amenities": ["wifi", "gym", "restaurant"],
        "notes": "Good value but far from venue — heavy Bangalore traffic, 55+ min commute daily",
    },
    {
        "id": "H3",
        "name": "Ibis Bangalore City Centre",
        "location": "City Centre",
        "price_per_night_inr": 6_900,
        "stars": 3,
        "distance_from_venue_km": 14.8,
        "travel_time_to_venue_mins": 50,
        "amenities": ["wifi", "restaurant"],
        "notes": "Budget option but City Centre location — very far from Whitefield venue, 50 min commute",
    },
    {
        "id": "H5",
        "name": "Novotel Whitefield",
        "location": "Whitefield",
        "price_per_night_inr": 9_200,
        "stars": 4,
        "distance_from_venue_km": 15.5,
        "travel_time_to_venue_mins": 52,
        "amenities": ["wifi", "pool", "restaurant"],
        "notes": "Whitefield area but far end of zone — 52 min to Prestige Tech Park with traffic",
    },
    {
        "id": "H4",
        "name": "Taj MG Road",
        "location": "MG Road",
        "price_per_night_inr": 18_000,
        "stars": 5,
        "distance_from_venue_km": 3.5,
        "travel_time_to_venue_mins": 15,
        "amenities": ["wifi", "spa", "restaurant", "pool", "bar", "concierge", "business_lounge"],
        "notes": "Premium — closest to venue, best for client meetings. OVER PREFERRED BUDGET.",
    },
]

# ---------------------------------------------------------------------------
# Meeting venue
# ---------------------------------------------------------------------------
MEETING_VENUE: dict = {
    "id": "V1",
    "name": "Prestige Tech Park",
    "location": "Whitefield, Bangalore",
    "area": "East Bangalore",
    "client": "Acme Corp",
}

# ---------------------------------------------------------------------------
# Day-by-day meeting agenda
# ---------------------------------------------------------------------------
MEETING_AGENDA: dict[str, list[str]] = {
    "Day 1": [
        "09:00 – Arrive at Prestige Tech Park",
        "09:30 – Client introductions and project kick-off",
        "11:00 – Product demo and requirements walkthrough",
        "13:00 – Working lunch with client team",
        "14:30 – Deep-dive technical workshop",
        "17:00 – Day 1 wrap-up and action items",
        "19:00 – Team dinner",
    ],
    "Day 2": [
        "09:00 – Architecture review session",
        "11:00 – Integration planning",
        "13:00 – Working lunch",
        "14:00 – Finalise deliverables and timelines",
        "15:30 – Client sign-off meeting",
        "16:30 – Depart for Bangalore airport",
        "18:30 – Flight back to Pune",
    ],
}

# ---------------------------------------------------------------------------
# Miscellaneous travel costs
# ---------------------------------------------------------------------------
MISC_COSTS: dict[str, int] = {
    "airport_transfer_inr": 1_200,   # cab to/from airport (each way)
    "local_transport_inr": 2_500,    # daily cabs to venue
    "meals_per_day_inr": 1_500,
    "incidentals_inr": 500,
}
