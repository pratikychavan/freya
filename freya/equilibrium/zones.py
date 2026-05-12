"""freya/equilibrium/zones.py

Operational Zone Management Engine.

Defines the six built-in operational zones, tracks their stability
independently, and supports asymmetric zone-level stabilization.
"""
from __future__ import annotations

from freya.equilibrium.models import EquilibriumState, OperationalEquilibriumZone

# ---------------------------------------------------------------------------
# Zone defaults — baseline pressure and state when system is at equilibrium
# ---------------------------------------------------------------------------
_ZONE_DEFAULTS: dict[str, dict] = {
    "governance": {
        "zone_name": "Governance Zone",
        "equilibrium_state": "stabilized",
        "pressure_level": 0.30,
        "stabilization_active": False,
        "recovery_stage": "complete",
    },
    "reasoning": {
        "zone_name": "Reasoning Zone",
        "equilibrium_state": "stabilized",
        "pressure_level": 0.35,
        "stabilization_active": False,
        "recovery_stage": "complete",
    },
    "optimization": {
        "zone_name": "Optimization Zone",
        "equilibrium_state": "stabilized",
        "pressure_level": 0.30,
        "stabilization_active": False,
        "recovery_stage": "complete",
    },
    "delegation": {
        "zone_name": "Delegation Zone",
        "equilibrium_state": "stabilized",
        "pressure_level": 0.25,
        "stabilization_active": False,
        "recovery_stage": "complete",
    },
    "recovery": {
        "zone_name": "Recovery Zone",
        "equilibrium_state": "stabilized",
        "pressure_level": 0.20,
        "stabilization_active": False,
        "recovery_stage": "complete",
    },
    "coordination": {
        "zone_name": "Coordination Zone",
        "equilibrium_state": "stabilized",
        "pressure_level": 0.28,
        "stabilization_active": False,
        "recovery_stage": "complete",
    },
}


def _state_from_pressure(pressure: float) -> EquilibriumState:
    if pressure >= 0.70:
        return "unstable"
    if pressure >= 0.50:
        return "recovering"
    if pressure >= 0.35:
        return "stabilized"
    return "restored"


def _recovery_stage_from_pressure(pressure: float) -> str:
    if pressure >= 0.70:
        return "early_mitigation"
    if pressure >= 0.50:
        return "stabilized"
    if pressure >= 0.35:
        return "recovering"
    if pressure >= 0.20:
        return "restoring"
    return "complete"


class OperationalZoneManagementEngine:
    """Creates and tracks the state of each operational equilibrium zone."""

    def all_zone_names(self) -> list[str]:
        return list(_ZONE_DEFAULTS.keys())

    def build_zone(
        self,
        zone_key: str,
        pressure_override: float | None = None,
        stabilization_active: bool | None = None,
    ) -> OperationalEquilibriumZone:
        """Build a zone with optional pressure and stabilization overrides."""
        defaults = dict(_ZONE_DEFAULTS.get(zone_key, _ZONE_DEFAULTS["coordination"]))
        # Use canonical zone_name even for unknown keys
        if zone_key not in _ZONE_DEFAULTS:
            defaults["zone_name"] = zone_key.replace("_", " ").title() + " Zone"

        pressure = pressure_override if pressure_override is not None else defaults["pressure_level"]
        state = _state_from_pressure(pressure)
        stage = _recovery_stage_from_pressure(pressure)
        active = stabilization_active if stabilization_active is not None else (pressure > 0.45)

        return OperationalEquilibriumZone(
            zone_name=defaults["zone_name"],
            equilibrium_state=state,
            pressure_level=pressure,
            stabilization_active=active,
            recovery_stage=stage,
        )

    def build_all_zones(
        self,
        pressure_map: dict[str, float] | None = None,
    ) -> dict[str, OperationalEquilibriumZone]:
        """Build all six zones, optionally overriding pressures via a map.

        Args:
            pressure_map: Optional {zone_key: pressure}. Missing keys use defaults.
        """
        pressure_map = pressure_map or {}
        return {
            key: self.build_zone(key, pressure_override=pressure_map.get(key))
            for key in _ZONE_DEFAULTS
        }

    def classify_zones(
        self, zones: dict[str, OperationalEquilibriumZone]
    ) -> tuple[list[str], list[str], list[str]]:
        """Classify zones into (unstable, recovering, stabilized_or_restored).

        Returns three lists of zone_name strings.
        """
        unstable: list[str] = []
        recovering: list[str] = []
        stabilized: list[str] = []
        for zone in zones.values():
            if zone.equilibrium_state == "unstable":
                unstable.append(zone.zone_name)
            elif zone.equilibrium_state == "recovering":
                recovering.append(zone.zone_name)
            else:
                stabilized.append(zone.zone_name)
        return unstable, recovering, stabilized
