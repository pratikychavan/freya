from __future__ import annotations

import time
from typing import Any, Literal

from freya.tracing.models import DAGTrace, EventType, TaskTrace, TraceEvent


class TraceManager:
    """Manages traces for a single DAG execution session."""

    def __init__(self, session_id: str | None = None) -> None:
        self._dag_trace = DAGTrace()
        if session_id:
            self._dag_trace.session_id = session_id

    # ------------------------------------------------------------------
    # Task lifecycle
    # ------------------------------------------------------------------

    def start_task(self, task_id: str) -> None:
        task_trace = TaskTrace(task_id=task_id, start_time=time.time())
        self._dag_trace.task_traces[task_id] = task_trace
        self._append(task_id, "task_started", {})

    def complete_task(
        self,
        task_id: str,
        status: Literal["SUCCESS", "FAILED"],
        error: str | None = None,
        token_usage: dict[str, Any] | None = None,
    ) -> None:
        trace = self._get(task_id)
        trace.end_time = time.time()
        trace.status = status
        trace.error = error
        trace.token_usage = token_usage

        event_type: EventType = "task_completed" if status == "SUCCESS" else "task_failed"
        payload: dict[str, Any] = {}
        if error:
            payload["error"] = error
        if token_usage:
            payload["token_usage"] = token_usage
        self._append(task_id, event_type, payload)

    # ------------------------------------------------------------------
    # Generic event log
    # ------------------------------------------------------------------

    def log_event(
        self,
        task_id: str,
        event_type: EventType,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._append(task_id, event_type, payload or {})

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_task_trace(self, task_id: str) -> TaskTrace:
        return self._get(task_id)

    def finalize(self, status: Literal["SUCCESS", "FAILED"]) -> None:
        self._dag_trace.end_time = time.time()
        self._dag_trace.status = status

    def export_dag_trace(self) -> dict[str, Any]:
        return self._dag_trace.model_dump()

    @property
    def dag_trace(self) -> DAGTrace:
        return self._dag_trace

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get(self, task_id: str) -> TaskTrace:
        trace = self._dag_trace.task_traces.get(task_id)
        if trace is None:
            raise KeyError(f"No trace found for task '{task_id}'.")
        return trace

    def _append(
        self, task_id: str, event_type: EventType, payload: dict[str, Any]
    ) -> None:
        event = TraceEvent(event_type=event_type, task_id=task_id, payload=payload)
        self._get(task_id).events.append(event)
