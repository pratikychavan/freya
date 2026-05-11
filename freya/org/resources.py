"""freya/org/resources.py

SharedOperationalResourceEngine

Tracks shared execution resources across workflows:
  - reasoning_budget
  - approval_bandwidth
  - delegation_pool
  - optimization_budget
"""
from __future__ import annotations

from freya.org.models import ContentionLevel, SharedOperationalResource

_CONTENTION_THRESHOLDS = {
    "none":     0.40,
    "low":      0.60,
    "moderate": 0.75,
    "high":     0.88,
    "severe":   1.01,   # >88% = severe
}


class SharedOperationalResourceEngine:
    """Manages shared resource pools across organizational workflows."""

    def __init__(self) -> None:
        self._resources: dict[str, SharedOperationalResource] = {}

    # ── Registration ──────────────────────────────────────────────────────────

    def register(
        self,
        resource_id: str,
        resource_type: str,
        total_capacity: float = 1.0,
    ) -> SharedOperationalResource:
        res = SharedOperationalResource(
            resource_id=resource_id,
            resource_type=resource_type,
            total_capacity=total_capacity,
        )
        self._resources[resource_id] = res
        return res

    def get(self, resource_id: str) -> SharedOperationalResource | None:
        return self._resources.get(resource_id)

    def all(self) -> list[SharedOperationalResource]:
        return list(self._resources.values())

    # ── Allocation ────────────────────────────────────────────────────────────

    def allocate(
        self, resource_id: str, workflow_id: str, share: float
    ) -> SharedOperationalResource:
        res = self._get_or_create(resource_id)
        allocated = dict(res.allocated)
        allocated[workflow_id] = share
        active = list(set(res.active_workflows + [workflow_id]))
        pressure = min(1.0, sum(allocated.values()) / max(res.total_capacity, 0.001))
        contention = self._contention_level(pressure)
        updated = res.model_copy(
            update={
                "allocated": allocated,
                "active_workflows": active,
                "resource_pressure": round(pressure, 3),
                "contention_level": contention,
            }
        )
        self._resources[resource_id] = updated
        return updated

    def release(self, resource_id: str, workflow_id: str) -> SharedOperationalResource:
        res = self._get_or_create(resource_id)
        allocated = {k: v for k, v in res.allocated.items() if k != workflow_id}
        active = [w for w in res.active_workflows if w != workflow_id]
        pressure = min(1.0, sum(allocated.values()) / max(res.total_capacity, 0.001))
        contention = self._contention_level(pressure)
        updated = res.model_copy(
            update={
                "allocated": allocated,
                "active_workflows": active,
                "resource_pressure": round(pressure, 3),
                "contention_level": contention,
            }
        )
        self._resources[resource_id] = updated
        return updated

    # ── Pressure analysis ─────────────────────────────────────────────────────

    def under_pressure(self, resource_id: str, threshold: float = 0.75) -> bool:
        res = self._resources.get(resource_id)
        if res is None:
            return False
        return res.resource_pressure >= threshold

    def pressure_summary(self) -> list[str]:
        lines: list[str] = []
        for res in self._resources.values():
            pct = int(res.resource_pressure * 100)
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            lines.append(
                f"{res.resource_id:<30} {bar} {pct:3d}%  [{res.contention_level}]"
            )
        return lines

    def contending_resources(self, threshold: float = 0.70) -> list[SharedOperationalResource]:
        return [r for r in self._resources.values() if r.resource_pressure >= threshold]

    # ── Private ────────────────────────────────────────────────────────────────

    def _get_or_create(self, resource_id: str) -> SharedOperationalResource:
        if resource_id not in self._resources:
            self._resources[resource_id] = SharedOperationalResource(
                resource_id=resource_id,
                resource_type="unknown",
            )
        return self._resources[resource_id]

    @staticmethod
    def _contention_level(pressure: float) -> ContentionLevel:
        if pressure >= 0.88:
            return "severe"
        if pressure >= 0.75:
            return "high"
        if pressure >= 0.60:
            return "moderate"
        if pressure >= 0.40:
            return "low"
        return "none"
