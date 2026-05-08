from __future__ import annotations

import logging
import traceback
from typing import Any

from pydantic import ValidationError

from freya.adapter import LLMAdapter
from freya.context import ExecutionContext
from freya.memory.store import InMemoryStore, MemoryStore
from freya.models import Task, TaskResult
from freya.policy.manager import PolicyManager
from freya.prompts.registry import PromptRegistry
from freya.registry import ToolRegistry
from freya.trace import Trace
from freya.tracing.manager import TraceManager

logger = logging.getLogger(__name__)


class ExecutionEngine:
    def __init__(
        self,
        llm_adapter: LLMAdapter,
        tool_registry: ToolRegistry,
        policy_manager: PolicyManager | None = None,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:
        self._llm = llm_adapter
        self._registry = tool_registry
        self._policy_manager = policy_manager
        self._prompt_registry = prompt_registry

    async def execute_task(
        self,
        task: Task,
        trace_manager: TraceManager | None = None,
        memory: MemoryStore | None = None,
        session_id: str | None = None,
    ) -> TaskResult:
        legacy_trace = Trace.start(task_id=task.task_id, input=task.input)

        if trace_manager:
            trace_manager.start_task(task.task_id)

        # Prefer the explicitly supplied session_id so that the worker can pass the
        # real session id from the fetched task.  Fall back to the trace manager's
        # dag_trace id for DAGRunner calls (all tasks share one TraceManager there).
        resolved_session_id = (
            session_id
            or (trace_manager.dag_trace.session_id if trace_manager else "")
        )
        context = ExecutionContext(
            session_id=resolved_session_id,
            task_id=task.task_id,
            memory=memory or InMemoryStore(),
        )
        policy_context = {
            "session_id": resolved_session_id,
            "task_id": task.task_id,
            "task_type": task.type,
        }

        try:
            # --- Pre-execution policy check ---
            if self._policy_manager:
                input_policy_results = self._policy_manager.evaluate_input(
                    task.model_dump(), policy_context
                )
                if trace_manager:
                    for pr in input_policy_results:
                        trace_manager.log_event(
                            task.task_id,
                            "policy_check",
                            {
                                "stage": "input",
                                "policy_name": pr.policy_name,
                                "action": pr.action,
                                "reason": pr.reason,
                            },
                        )
                if self._policy_manager.is_blocked(input_policy_results):
                    block_reason = next(
                        r.reason for r in input_policy_results if r.action == "BLOCK"
                    )
                    error_msg = f"PolicyBlock: {block_reason}"
                    legacy_trace.finish(error=error_msg)
                    if trace_manager:
                        trace_manager.complete_task(task.task_id, "FAILED", error=error_msg)
                    return TaskResult(
                        task_id=task.task_id,
                        status="FAILED",
                        output=None,
                        error=error_msg,
                        error_type="POLICY_BLOCK",
                        duration_ms=legacy_trace.duration_ms,
                        trace=legacy_trace,
                    )

            # --- Execution ---
            if task.type == "llm":
                if trace_manager and not task.input.get("prompt_name"):
                    # For raw prompts log here; registry prompts log inside _execute_llm.
                    trace_manager.log_event(task.task_id, "llm_call_started", {"input": task.input})
                output = await self._execute_llm(task.input, task_id=task.task_id, trace_manager=trace_manager)
                token_usage = output.get("usage")
                if trace_manager:
                    trace_manager.log_event(task.task_id, "llm_call_completed", {"usage": token_usage})
            elif task.type == "tool":
                tool_name = task.input.get("tool_name", "")
                if trace_manager:
                    trace_manager.log_event(task.task_id, "tool_call_started", {"tool_name": tool_name})
                output = await self._execute_tool(task.input, context, trace_manager)
                token_usage = None
                if trace_manager:
                    trace_manager.log_event(task.task_id, "tool_call_completed", {"tool_name": tool_name})
            else:
                raise ValueError(f"Unknown task type: {task.type!r}")

            # --- Post-execution policy check ---
            if self._policy_manager:
                output_policy_results = self._policy_manager.evaluate_output(
                    task.model_dump(), output, policy_context
                )
                if trace_manager:
                    for pr in output_policy_results:
                        trace_manager.log_event(
                            task.task_id,
                            "policy_check",
                            {
                                "stage": "output",
                                "policy_name": pr.policy_name,
                                "action": pr.action,
                                "reason": pr.reason,
                            },
                        )
                if self._policy_manager.is_blocked(output_policy_results):
                    block_reason = next(
                        r.reason for r in output_policy_results if r.action == "BLOCK"
                    )
                    error_msg = f"PolicyBlock (output): {block_reason}"
                    legacy_trace.finish(error=error_msg)
                    if trace_manager:
                        trace_manager.complete_task(task.task_id, "FAILED", error=error_msg)
                    return TaskResult(
                        task_id=task.task_id,
                        status="FAILED",
                        output=None,
                        error=error_msg,
                        error_type="POLICY_BLOCK",
                        duration_ms=legacy_trace.duration_ms,
                        trace=legacy_trace,
                    )

            legacy_trace.finish(output=output, token_usage=token_usage)
            if trace_manager:
                trace_manager.complete_task(task.task_id, "SUCCESS", token_usage=token_usage)

            return TaskResult(
                task_id=task.task_id,
                status="SUCCESS",
                output=output,
                error=None,
                duration_ms=legacy_trace.duration_ms,
                trace=legacy_trace,
            )

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            error_type = _classify_error(exc)
            legacy_trace.finish(error=error_msg)
            if trace_manager:
                trace_manager.complete_task(task.task_id, "FAILED", error=error_msg)

            return TaskResult(
                task_id=task.task_id,
                status="FAILED",
                output=None,
                error=error_msg,
                error_type=error_type,
                duration_ms=legacy_trace.duration_ms,
                trace=legacy_trace,
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _execute_llm(
        self,
        input: dict[str, Any],
        task_id: str | None = None,
        trace_manager: TraceManager | None = None,
    ) -> dict[str, Any]:
        """Resolve prompt (from registry or raw) then call the LLM adapter."""
        llm_input = dict(input)

        prompt_name: str | None = llm_input.pop("prompt_name", None)
        if prompt_name:
            if self._prompt_registry is None:
                raise ValueError(
                    f"Task references prompt '{prompt_name}' but no PromptRegistry "
                    "was supplied to ExecutionEngine."
                )
            variables: dict[str, Any] = llm_input.pop("variables", {})
            prompt = self._prompt_registry.get(prompt_name, variables)
            rendered = prompt.render()

            if trace_manager and task_id:
                trace_manager.log_event(
                    task_id,
                    "llm_call_started",
                    {
                        "prompt_name": prompt_name,
                        "template": prompt.template,
                        "variables": prompt.variables,
                        "rendered_prompt": rendered,
                    },
                )

            llm_input["prompt"] = rendered
            if prompt.system:
                llm_input["system"] = prompt.system
        
        return await self._llm.complete(llm_input)

    async def _execute_tool(
        self,
        input: dict[str, Any],
        context: ExecutionContext,
        trace_manager: TraceManager | None = None,
    ) -> dict[str, Any]:
        tool_name: str = input.get("tool_name", "")
        tool_input: dict[str, Any] = input.get("tool_input", {})

        tool = self._registry.get(tool_name)

        # --- Input validation ---
        try:
            validated_input = tool.input_model.model_validate(tool_input)
        except ValidationError as exc:
            raise ValueError(f"Input validation failed for tool '{tool_name}': {exc}") from exc

        # Wrap memory with tracing if trace_manager is present
        traced_memory = (
            _TracingMemoryStore(context.memory, context.task_id, trace_manager)
            if trace_manager
            else context.memory
        )
        traced_context = ExecutionContext(
            session_id=context.session_id,
            task_id=context.task_id,
            memory=traced_memory,
        )

        # --- Execution ---
        raw_result = await tool.execute(validated_input, traced_context)

        # --- Output validation ---
        try:
            validated_output = tool.output_model.model_validate(
                raw_result if isinstance(raw_result, dict) else raw_result.model_dump()
            )
        except ValidationError as exc:
            raise ValueError(f"Output validation failed for tool '{tool_name}': {exc}") from exc

        return validated_output.model_dump()


def _classify_error(exc: Exception) -> str:
    """Map exception types to structured error categories."""
    msg = str(exc)
    if isinstance(exc, KeyError) and "not registered" in msg:
        return "TOOL_NOT_FOUND"
    if isinstance(exc, ValueError):
        if "validation failed" in msg.lower():
            return "VALIDATION_ERROR"
        if "policyblock" in msg.lower():
            return "POLICY_BLOCK"
    return "EXECUTION_ERROR"


_MEM_VALUE_MAX = 200


def _truncate_value(value: Any) -> dict[str, Any]:
    """Serialize value for trace logging, truncating if over _MEM_VALUE_MAX chars."""
    as_str = str(value)
    if len(as_str) > _MEM_VALUE_MAX:
        return {"value": as_str[:_MEM_VALUE_MAX], "truncated": True}
    return {"value": value, "truncated": False}


class _TracingMemoryStore(MemoryStore):
    """Thin wrapper that logs memory_access events into the trace."""

    def __init__(
        self,
        inner: MemoryStore,
        task_id: str,
        trace_manager: TraceManager,
    ) -> None:
        self._inner = inner
        self._task_id = task_id
        self._tm = trace_manager

    def get(self, session_id: str, key: str) -> Any:
        value = self._inner.get(session_id, key)
        payload = {"action": "get", "key": key, **_truncate_value(value)}
        self._tm.log_event(self._task_id, "memory_access", payload)
        return value

    def set(self, session_id: str, key: str, value: Any) -> None:
        self._inner.set(session_id, key, value)
        payload = {"action": "set", "key": key, **_truncate_value(value)}
        self._tm.log_event(self._task_id, "memory_access", payload)

    def delete(self, session_id: str, key: str) -> None:
        self._inner.delete(session_id, key)

    def list_keys(self, session_id: str) -> list[str]:
        return self._inner.list_keys(session_id)

    def cleanup_session(self, session_id: str) -> None:
        self._inner.cleanup_session(session_id)
