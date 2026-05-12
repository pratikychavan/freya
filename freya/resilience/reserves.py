"""freya/resilience/reserves.py

Operational Resilience Reserve Engine.

Tracks adaptive capacity depletion for each stabilization technique,
estimates future stabilization headroom, and recommends replenishment
pacing. Treats adaptation capacity as finite — reserves must be
preserved for high-severity events.
"""
from __future__ import annotations

from freya.resilience.models import DepletionRisk, OperationalResilienceReserve


# ---------------------------------------------------------------------------
# Reserve profiles — describe each stabilization technique's finite capacity
# ---------------------------------------------------------------------------

_RESERVE_PROFILES: dict[str, dict] = {
    "compression": {
        "label": "Reasoning Compression Reserve",
        "depletion_description": (
            "Each compression cycle consumes analytical trust headroom. "
            "Sustained use degrades output quality confidence."
        ),
        "replenishment": (
            "Reduce compression frequency for 2+ cycles; "
            "restore with batching or reservation as bridge techniques."
        ),
    },
    "batching": {
        "label": "Governance Batching Reserve",
        "depletion_description": (
            "Sustained batching accumulates review latency, "
            "reducing effective governance throughput."
        ),
        "replenishment": (
            "Taper batching window size; introduce priority-lane review "
            "slots to restore throughput before fully removing batching."
        ),
    },
    "smoothing": {
        "label": "Operational Smoothing Reserve",
        "depletion_description": (
            "Prolonged smoothing obscures root causes, "
            "degrading operational transparency and accountability."
        ),
        "replenishment": (
            "Transition to transparent root-cause interventions (batching, "
            "sequencing). Allow smoothing to lapse naturally — do not abruptly remove."
        ),
    },
    "governance_review": {
        "label": "Governance Review Capacity Reserve",
        "depletion_description": (
            "High-frequency governance reviews consume review board capacity, "
            "risking governance fatigue and review quality degradation."
        ),
        "replenishment": (
            "Batch low-priority reviews; defer non-critical reviews by 1 cycle. "
            "Reserve escalation slots for critical decisions."
        ),
    },
    "recovery_sequencing": {
        "label": "Recovery Sequencing Flexibility Reserve",
        "depletion_description": (
            "Repeated use of the same recovery path reduces coordination "
            "diversity, creating brittleness if the primary path degrades."
        ),
        "replenishment": (
            "Validate and warm an alternate recovery path. "
            "Rotate primary/secondary paths each 3–4 cycles."
        ),
    },
    "reservation": {
        "label": "Capacity Reservation Reserve",
        "depletion_description": (
            "Long-running reservations lock capacity, reducing operational "
            "flexibility for future workload surges."
        ),
        "replenishment": (
            "Release non-critical reservations at cycle 6; "
            "review reservation scope before each renewal."
        ),
    },
}

# Capacity decay table: usage_cycles → remaining_capacity
_CAPACITY_TABLE: list[tuple[int, int, float]] = [
    (0, 2,  0.85),
    (3, 4,  0.55),
    (5, 6,  0.30),
    (7, 99, 0.10),
]


def _capacity_for_cycles(usage_cycles: int) -> float:
    for lo, hi, cap in _CAPACITY_TABLE:
        if lo <= usage_cycles <= hi:
            return cap
    return 0.10


def _depletion_risk(capacity: float) -> DepletionRisk:
    if capacity >= 0.70:
        return "low"
    if capacity >= 0.45:
        return "moderate"
    if capacity >= 0.20:
        return "high"
    return "critical"


class OperationalResilienceReserveEngine:
    """Assesses adaptive capacity depletion for operational stabilization reserves."""

    def assess_reserve(
        self,
        reserve_type: str,
        usage_cycles: int,
        confidence: float = 0.70,
    ) -> OperationalResilienceReserve:
        """Return an OperationalResilienceReserve for a given technique and usage cycles.

        Parameters
        ----------
        reserve_type:
            The stabilization technique identifier (e.g. "compression", "batching").
        usage_cycles:
            Number of consecutive cycles this technique has been active.
        confidence:
            Analytical confidence — low confidence shifts capacity estimate down slightly.
        """
        profile = _RESERVE_PROFILES.get(reserve_type)
        if profile is None:
            # Unknown reserve type — treat conservatively
            capacity = max(0.10, 0.70 - usage_cycles * 0.10)
            return OperationalResilienceReserve(
                reserve_type=reserve_type,
                current_capacity=round(capacity, 2),
                depletion_risk=_depletion_risk(capacity),
                replenishment_strategy=(
                    "Unknown technique. Reduce usage frequency and assess "
                    "impact before continuing."
                ),
            )

        capacity = _capacity_for_cycles(usage_cycles)

        # Low confidence → reduce capacity estimate by 10 pp (more conservative)
        if confidence < 0.55:
            capacity = max(0.05, capacity - 0.10)

        risk = _depletion_risk(capacity)

        return OperationalResilienceReserve(
            reserve_type=reserve_type,
            current_capacity=round(capacity, 2),
            depletion_risk=risk,
            replenishment_strategy=profile["replenishment"],
        )

    def assess_all(
        self,
        active_interventions: dict[str, int],
        confidence: float = 0.70,
    ) -> list[OperationalResilienceReserve]:
        """Return reserves for all active interventions.

        Parameters
        ----------
        active_interventions:
            Mapping of intervention name → usage_cycles.
        """
        return [
            self.assess_reserve(intervention, cycles, confidence)
            for intervention, cycles in active_interventions.items()
        ]

    def critical_reserves(
        self, reserves: list[OperationalResilienceReserve]
    ) -> list[OperationalResilienceReserve]:
        """Return only reserves at critical or high depletion risk."""
        return [r for r in reserves if r.depletion_risk in ("critical", "high")]

    def overall_depletion_risk(
        self, reserves: list[OperationalResilienceReserve]
    ) -> DepletionRisk:
        """Return the highest depletion risk across all reserves."""
        order = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
        if not reserves:
            return "low"
        return max(reserves, key=lambda r: order[r.depletion_risk]).depletion_risk
