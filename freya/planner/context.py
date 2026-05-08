from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from freya.planner.mode import PlanningMode
from freya.planner.observation import Observation

if TYPE_CHECKING:
    from freya.planner.capabilities import ToolCapability
    from freya.planner.prompt_capabilities import PromptCapability


class PlanningContext(BaseModel):
    """Shared state passed to the planner at every iteration."""

    model_config = {"arbitrary_types_allowed": True}

    session_id: str
    goal: str
    planning_mode: PlanningMode = PlanningMode.DETERMINISTIC
    completed_tasks: list[str] = Field(default_factory=list)
    failed_tasks: list[str] = Field(default_factory=list)
    task_results: dict[str, Any] = Field(default_factory=dict)
    memory_snapshot: dict[str, Any] = Field(default_factory=dict)
    trace_summary: dict[str, Any] = Field(default_factory=dict)
    iteration_count: int = 0
    available_tools: list[Any] = Field(
        default_factory=list,
        description="ToolCapability objects exported from the ToolRegistry.",
    )
    available_prompt_capabilities: list[Any] = Field(
        default_factory=list,
        description="PromptCapability objects — only populated in COGNITIVE mode.",
    )
    recent_observations: list[Observation] = Field(
        default_factory=list,
        description="Ordered list of observations from completed tasks.",
    )
    child_workflow_summaries: list[str] = Field(
        default_factory=list,
        description="Summarized outcomes of delegated child workflows.",
    )

    # ------------------------------------------------------------------
    # Observation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize execution state only.

        ``available_tools`` and ``available_prompt_capabilities`` are live
        runtime objects and are intentionally excluded — they must be
        reattached by the caller after restoration.
        """
        return self.model_dump(mode="json", exclude={"available_tools", "available_prompt_capabilities"})

    @classmethod
    def from_dict(cls, data: dict) -> "PlanningContext":
        """Reconstruct execution state.  Runtime capabilities are not restored
        by this method — the caller is responsible for reattaching them.
        """
        data = dict(data)
        data.setdefault("available_tools", [])
        data.setdefault("available_prompt_capabilities", [])
        return cls.model_validate(data)

    def latest_success(self) -> Observation | None:
        """Return the most recent successful observation, or None."""
        for obs in reversed(self.recent_observations):
            if obs.status == "SUCCESS":
                return obs
        return None

    def latest_failure(self) -> Observation | None:
        """Return the most recent failed observation, or None."""
        for obs in reversed(self.recent_observations):
            if obs.status == "FAILED":
                return obs
        return None

    def summarize_observations(self) -> list[str]:
        """Return compact planner-friendly observation summaries."""
        return [obs.as_summary() for obs in self.recent_observations]
