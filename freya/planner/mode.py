from __future__ import annotations

from enum import Enum


class PlanningMode(str, Enum):
    DETERMINISTIC = "deterministic"
    COGNITIVE = "cognitive"
