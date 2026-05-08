from __future__ import annotations

EXPENSES: list[dict] = [
    {"category": "Coffee supplies", "amount": 15.0},
    {"category": "Office snacks",   "amount": 25.0},
    {"category": "Team lunch",      "amount": 60.0},
]

AMOUNTS: list[float] = [e["amount"] for e in EXPENSES]
