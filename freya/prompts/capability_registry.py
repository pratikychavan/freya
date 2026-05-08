from __future__ import annotations

from freya.planner.mode import PlanningMode
from freya.planner.prompt_capabilities import PromptCapability


class PromptCapabilityRegistry:
    """In-memory registry for planner-visible prompt capabilities.

    Separate from ToolRegistry and PromptRegistry — this registry exposes
    *reasoning operations* (not tool actions, not raw prompt templates) to
    the planner so it can select and orchestrate cognition tasks.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, PromptCapability] = {}

    def register(self, capability: PromptCapability) -> None:
        """Register a PromptCapability.  Raises ValueError on duplicate name."""
        if capability.name in self._capabilities:
            raise ValueError(
                f"PromptCapability '{capability.name}' is already registered."
            )
        self._capabilities[capability.name] = capability

    def list_capabilities(
        self, mode: PlanningMode | None = None
    ) -> list[PromptCapability]:
        """Return all capabilities, optionally filtered to those matching *mode*."""
        caps = list(self._capabilities.values())
        if mode is not None:
            caps = [c for c in caps if c.planning_mode == mode]
        return caps

    def get(self, name: str) -> PromptCapability:
        """Return a capability by name.  Raises KeyError if not found."""
        if name not in self._capabilities:
            raise KeyError(f"PromptCapability '{name}' not found in registry.")
        return self._capabilities[name]
