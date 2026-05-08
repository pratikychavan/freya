from __future__ import annotations

import json
from typing import Any

from freya.planner.context import PlanningContext


def build_planner_context(context: PlanningContext) -> dict[str, Any]:
    """Compress a PlanningContext into a prompt-safe dict.

    Rules:
    - Includes goal, mode, recent observation summaries, memory summary.
    - Includes capability names only (not full schemas) to prevent prompt bloat.
    - Excludes raw traces, full memory dumps, and stale task history.
    """
    observation_summaries = [
        obs.as_summary() for obs in context.recent_observations[-10:]
    ]

    # Memory summary: keep only string/numeric leaves, skip large blobs.
    memory_summary: dict[str, Any] = {}
    for k, v in context.memory_snapshot.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            memory_summary[k] = v
        else:
            memory_summary[k] = f"<{type(v).__name__}>"

    tool_names = [cap.name for cap in context.available_tools]

    prompt_cap_names = [cap.name for cap in context.available_prompt_capabilities]

    return {
        "goal": context.goal,
        "planning_mode": context.planning_mode.value,
        "recent_observation_summaries": observation_summaries,
        "memory_summary": memory_summary,
        "available_tool_names": tool_names,
        "available_prompt_capability_names": prompt_cap_names,
        "completed_tasks": context.completed_tasks,
        "failed_tasks": context.failed_tasks,
    }


def build_planner_context_json(context: PlanningContext) -> str:
    """Serialise the compressed context as a JSON string."""
    return json.dumps(build_planner_context(context), indent=2)
