from __future__ import annotations

import json
import logging
from typing import Any

from freya.adapter import LLMAdapter
from freya.dag.models import DAG
from freya.planner.base import BasePlanner
from freya.planner.context import PlanningContext
from freya.planner.context_builder import build_planner_context
from freya.planner.mode import PlanningMode
from freya.prompts.registry import PromptRegistry

logger = logging.getLogger(__name__)

# The PromptRegistry key that must be registered before using SimpleIterativePlanner.
PLAN_NEXT_PROMPT = "plan_next"


# Prompt registry key for the repair prompt (optional — falls back to plan_next).
PLAN_REPAIR_PROMPT = "plan_repair"

# Prompt registry key for the runtime recovery prompt (optional — falls back to inline).
PLAN_RECOVERY_PROMPT = "plan_recovery"


class SimpleIterativePlanner(BasePlanner):
    """Uses an LLM and a PromptRegistry to generate DAG fragments iteratively.

    The registered prompt named ``plan_next`` is rendered with the current
    PlanningContext and sent to the LLM.  The LLM must return a JSON object
    matching the DAG schema (``{"tasks": [...]}``) — or ``{"tasks": []}`` to
    signal that the goal is complete.

    Planning decisions derive from runtime observations — NOT from iteration order.
    """

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        prompt_registry: PromptRegistry,
    ) -> None:
        self._llm = llm_adapter
        self._prompts = prompt_registry

    async def plan_next(self, context: PlanningContext) -> DAG:
        compressed = build_planner_context(context)

        tools_block = _render_tool_capabilities(context.available_tools)
        observations_block = _render_observations(compressed["recent_observation_summaries"])
        memory_block = json.dumps(compressed["memory_summary"])

        variables: dict[str, Any] = {
            "goal": context.goal,
            "recent_observations": observations_block,
            "memory_summary": memory_block,
            "completed_tasks": json.dumps(compressed["completed_tasks"]),
            "failed_tasks": json.dumps(compressed["failed_tasks"]),
            "available_tools": tools_block,
        }

        if context.planning_mode == PlanningMode.COGNITIVE:
            variables["available_prompt_capabilities"] = _render_prompt_capabilities(
                context.available_prompt_capabilities
            )
        else:
            variables["available_prompt_capabilities"] = ""

        prompt = self._prompts.get(PLAN_NEXT_PROMPT, variables)
        rendered = prompt.render()

        response = await self._llm.complete(
            {
                "prompt": rendered,
                "system": prompt.system or "You are a planning assistant. Return only valid JSON.",
            }
        )

        raw_text: str = response.get("text", "")
        logger.debug("Planner LLM raw response: %s", raw_text[:300])

        try:
            data = _extract_json(raw_text)
            return DAG.model_validate(data)
        except Exception as exc:
            raise ValueError(
                f"Planner LLM returned an unparseable DAG at iteration "
                f"{context.iteration_count}: {exc}\nRaw: {raw_text[:300]}"
            ) from exc

    async def repair_dag(
        self,
        context: PlanningContext,
        broken_dag: DAG,
        validation_issues_text: str,
    ) -> DAG:
        """Ask the LLM to repair a broken DAG fragment."""
        compressed = build_planner_context(context)
        observations_block = _render_observations(compressed["recent_observation_summaries"])

        # Use a dedicated repair prompt if registered; fall back to a raw prompt string.
        try:
            prompt = self._prompts.get(
                PLAN_REPAIR_PROMPT,
                {
                    "validation_issues": validation_issues_text,
                    "recent_observations": observations_block,
                    "available_tools": _render_tool_capabilities(context.available_tools),
                },
            )
            rendered = prompt.render()
            system = prompt.system or "You are a planning assistant. Return only valid JSON."
        except KeyError:
            # No repair prompt registered — construct a fallback inline prompt.
            rendered = (
                f"The following DAG fragment was rejected by the validator:\n\n"
                f"Validation issues:\n{validation_issues_text}\n\n"
                f"Recent observations:\n{observations_block}\n\n"
                f"Available tools:\n{_render_tool_capabilities(context.available_tools)}\n\n"
                "Repair ONLY this fragment. Return corrected DAG JSON."
            )
            system = "You are a planning assistant. Return only valid JSON."

        response = await self._llm.complete({"prompt": rendered, "system": system})
        raw_text: str = response.get("text", "")
        logger.debug("Repair LLM response: %s", raw_text[:300])
        try:
            data = _extract_json(raw_text)
            return DAG.model_validate(data)
        except Exception as exc:
            raise ValueError(
                f"Planner LLM returned unparseable repair DAG: {exc}\nRaw: {raw_text[:300]}"
            ) from exc

    async def plan_recovery(
        self,
        context: PlanningContext,
        failed_observations: list[Any],
    ) -> DAG:
        """Generate a targeted recovery DAG fragment for runtime-failed tasks."""
        compressed = build_planner_context(context)
        observations_block = _render_observations(compressed["recent_observation_summaries"])
        tools_block = _render_tool_capabilities(context.available_tools)

        failures_block = "\n".join(
            f"  - {o.task_id} failed due to {o.failure_category or 'UNKNOWN'}: "
            f"{(o.error or 'no details')[:120]}"
            for o in failed_observations
        )

        try:
            prompt = self._prompts.get(
                PLAN_RECOVERY_PROMPT,
                {
                    "goal": context.goal,
                    "completed_tasks": json.dumps(compressed["completed_tasks"]),
                    "recoverable_failures": failures_block,
                    "recent_observations": observations_block,
                    "available_tools": tools_block,
                },
            )
            rendered = prompt.render()
            system = prompt.system or "You are a planning assistant. Return only valid JSON."
        except KeyError:
            rendered = (
                f"Goal: {context.goal}\n\n"
                f"Completed tasks (DO NOT regenerate): "
                f"{json.dumps(compressed['completed_tasks'])}\n\n"
                f"Recoverable runtime failures:\n{failures_block}\n\n"
                f"Recent observations:\n{observations_block}\n\n"
                f"Available tools:\n{tools_block}\n\n"
                "Generate a targeted recovery DAG for ONLY the failed task(s).\n"
                "Do NOT include tasks that already succeeded.\n"
                'Return JSON: {"tasks": [...]}'
            )
            system = "You are a planning assistant. Return only valid JSON."

        response = await self._llm.complete({"prompt": rendered, "system": system})
        raw_text: str = response.get("text", "")
        logger.debug("Recovery LLM response: %s", raw_text[:300])
        try:
            data = _extract_json(raw_text)
            return DAG.model_validate(data)
        except Exception as exc:
            raise ValueError(
                f"Planner LLM returned unparseable recovery DAG: {exc}\nRaw: {raw_text[:300]}"
            ) from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_tool_capabilities(caps: list[Any]) -> str:
    """Render a list of ToolCapability objects into a plain-text block."""
    if not caps:
        return "(no tools registered)"
    lines = []
    for i, cap in enumerate(caps, 1):
        lines.append(f"{i}. {cap.as_prompt_text()}")
    return "\n".join(lines)


def _render_observations(summaries: list[str]) -> str:
    """Render a list of observation summary strings into a numbered block."""
    if not summaries:
        return "(no observations yet)"
    return "\n".join(f"  - {s}" for s in summaries)


def _render_prompt_capabilities(caps: list[Any]) -> str:
    """Render a list of PromptCapability objects into a plain-text block."""
    if not caps:
        return "(no prompt capabilities registered)"
    lines = []
    for cap in caps:
        lines.append(cap.as_prompt_text())
    return "\n".join(lines)


def _extract_json(text: str) -> Any:
    """Parse JSON from LLM output, stripping optional markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1 if lines[-1].strip().startswith("```") else len(lines)
        text = "\n".join(lines[1:end]).strip()
    return json.loads(text)
