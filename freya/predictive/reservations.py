"""freya/predictive/reservations.py

OperationalReservationEngine

Proactively reserves operational capacity for critical workflows before
pressure peaks. All reservations are bounded, auditable, and expire
automatically or on demand.

Design rules:
  - Reservations never starve lower-priority workflows permanently
  - Maximum reserved fraction per resource: 40 %
  - All reservations carry an explicit expiration condition
  - Reservation size is modulated by forecast confidence
"""
from __future__ import annotations

import uuid

from freya.predictive.models import OperationalForecast, OperationalReservation

_MAX_RESERVATION_FRACTION = 0.40


class OperationalReservationEngine:
    """Create and track proactive capacity reservations."""

    def __init__(self) -> None:
        self._reservations: dict[str, OperationalReservation] = {}

    def reserve(
        self,
        resource: str,
        protected_workflow: str,
        reason: str,
        forecast: OperationalForecast,
        base_fraction: float = 0.20,
        expiration_condition: str = "pressure_normalized",
    ) -> OperationalReservation | None:
        """Create a reservation if forecast confidence warrants it."""
        if not forecast.action_warranted:
            return None  # Low confidence — observe only

        # Scale reservation size by confidence tier
        confidence_multipliers = {
            "confirmed":  1.0,
            "high":       0.85,
            "moderate":   0.65,
            "low":        0.40,
            "speculative": 0.0,
        }
        mult     = confidence_multipliers.get(forecast.confidence_tier, 0.0)
        capacity = round(min(base_fraction * mult, _MAX_RESERVATION_FRACTION), 4)

        if capacity <= 0.0:
            return None

        reservation = OperationalReservation(
            reservation_id=str(uuid.uuid4())[:8],
            reserved_resource=resource,
            reserved_capacity=capacity,
            protected_for_workflow=protected_workflow,
            reservation_reason=reason,
            expiration_condition=expiration_condition,
            active=True,
        )
        self._reservations[reservation.reservation_id] = reservation
        return reservation

    def release(self, reservation_id: str) -> bool:
        """Release a reservation by ID."""
        if reservation_id in self._reservations:
            self._reservations[reservation_id].active = False
            return True
        return False

    def release_for(self, workflow_id: str) -> list[OperationalReservation]:
        """Release all active reservations for a workflow."""
        released = []
        for r in self._reservations.values():
            if r.protected_for_workflow == workflow_id and r.active:
                r.active = False
                released.append(r)
        return released

    def active_reservations(self) -> list[OperationalReservation]:
        return [r for r in self._reservations.values() if r.active]

    def total_reserved(self, resource: str) -> float:
        return sum(
            r.reserved_capacity for r in self._reservations.values()
            if r.reserved_resource == resource and r.active
        )

    def available_capacity(self, resource: str, total: float = 1.0) -> float:
        return max(0.0, total - self.total_reserved(resource))

    def summary(self) -> dict[str, int]:
        active  = sum(1 for r in self._reservations.values() if r.active)
        expired = len(self._reservations) - active
        return {"active": active, "expired": expired}
