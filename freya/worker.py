from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from freya.engine import ExecutionEngine
from freya.memory.store import InMemoryStore
from freya.models import Task
from freya.transport.base import ControlPlaneTransport
from freya.tracing.manager import TraceManager

logger = logging.getLogger(__name__)

_MAX_SUBMIT_RETRIES = 3
_BACKOFF_INITIAL = 0.1
_BACKOFF_MAX = 5.0
_SESSION_TTL_SECONDS = 60.0


class Worker:
    def __init__(
        self,
        worker_id: str,
        transport: ControlPlaneTransport,
        engine: ExecutionEngine,
        poll_interval: float = 1.0,
    ) -> None:
        self._worker_id = worker_id
        self._transport = transport
        self._engine = engine
        self._poll_interval = poll_interval
        # Shared memory store — sessions isolated by session_id key
        self._memory = InMemoryStore()
        self._running = False
        # Local session lock — prevents concurrent execution of the same session on this worker.
        self._active_sessions: set[str] = set()
        # Idempotency cache (in-memory only). Persistence must be owned by the control plane
        # for true multi-worker idempotency guarantees.
        self._executed_tasks: dict[str, dict] = {}
        # TTL cleanup: records monotonic last-access time per session.
        self._session_last_access: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, max_iterations: int | None = None) -> None:
        """Pull tasks in a loop. Stops after max_iterations cycles (None = forever)."""
        self._running = True
        iteration = 0
        sleep_time = _BACKOFF_INITIAL  # Fix 3: exponential backoff state

        while self._running:
            if max_iterations is not None and iteration >= max_iterations:
                break
            iteration += 1

            await self._safe_heartbeat()

            task_dict = await self._safe_fetch()

            if task_dict is None:
                # Fix 3: exponential backoff on idle
                logger.info(
                    "[Worker %s] No tasks — sleeping %.2fs",
                    self._worker_id, sleep_time,
                )
                await asyncio.sleep(sleep_time)
                sleep_time = min(_BACKOFF_MAX, sleep_time * 2)
                continue

            # Task found — reset backoff
            sleep_time = _BACKOFF_INITIAL

            task_id = task_dict.get("task_id", "unknown")
            session_id = task_dict.get("session_id", task_id)

            # Fix 3: local session lock — skip if same session is already executing
            if session_id in self._active_sessions:
                logger.warning(
                    "[Worker %s] Session %s already active — skipping task %s (Fix 4: will retry next poll)",
                    self._worker_id, session_id, task_id,
                )
                # Fix 4: re-enqueue so the task gets picked up once the session is free
                await asyncio.sleep(0.05)
                continue

            # Idempotency — re-submit without re-executing
            if task_id in self._executed_tasks:
                logger.info(
                    "[Worker %s] Task %s already executed — resubmitting cached result",
                    self._worker_id, task_id,
                )
                await self._safe_submit(task_id, self._executed_tasks[task_id])
                continue

            logger.info(
                "[Worker %s] Fetched task=%s session=%s",
                self._worker_id, task_id, session_id,
            )

            # Update TTL timestamp on every access.
            self._session_last_access[session_id] = time.monotonic()

            self._active_sessions.add(session_id)
            try:
                result_dict, trace_dict = await self._execute(task_dict, session_id)
            finally:
                self._active_sessions.discard(session_id)

            payload = {**result_dict, "trace": trace_dict}
            self._executed_tasks[task_id] = payload
            await self._safe_submit(task_id, payload)

            # --- Cleanup strategy A: terminal flag ---
            if task_dict.get("is_terminal"):
                self._cleanup_session(session_id, reason="terminal")
            else:
                # --- Cleanup strategy B: TTL sweep for other sessions ---
                self._sweep_expired_sessions()


    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Session memory cleanup helpers
    # ------------------------------------------------------------------

    def _cleanup_session(self, session_id: str, reason: str) -> None:
        """Clean up memory for a session and remove all tracking state."""
        self._memory.cleanup_session(session_id)
        self._session_last_access.pop(session_id, None)
        remaining = self._memory.list_keys(session_id)
        logger.info(
            "[Worker %s] memory_cleanup session=%s reason=%s remaining_keys=%d",
            self._worker_id, session_id, reason, len(remaining),
        )

    def _sweep_expired_sessions(self) -> None:
        """Clean up sessions that have been idle longer than _SESSION_TTL_SECONDS."""
        now = time.monotonic()
        expired = [
            sid
            for sid, last in self._session_last_access.items()
            if now - last >= _SESSION_TTL_SECONDS and sid not in self._active_sessions
        ]
        for sid in expired:
            self._cleanup_session(sid, reason="ttl")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _execute(self, task_dict: dict, session_id: str) -> tuple[dict, dict]:
        trace_manager = TraceManager()
        try:
            task = Task(
                task_id=task_dict["task_id"],
                type=task_dict["type"],
                input=task_dict.get("input", {}),
                config=task_dict.get("config", {}),
            )
            # Debug: log memory keys before execution
            keys_before = self._memory.list_keys(session_id)
            logger.debug(
                "[Worker %s] memory_keys BEFORE task=%s session=%s keys=%s",
                self._worker_id, task_dict["task_id"], session_id, keys_before,
            )
            result = await self._engine.execute_task(
                task,
                trace_manager=trace_manager,
                memory=self._memory,
                session_id=session_id,
            )
            # Debug: log memory keys after execution
            keys_after = self._memory.list_keys(session_id)
            logger.debug(
                "[Worker %s] memory_keys AFTER task=%s session=%s keys=%s",
                self._worker_id, task_dict["task_id"], session_id, keys_after,
            )
            trace_manager.finalize(result.status)
            result_dict = {
                "status": result.status,
                "output": result.output,
                "error": result.error,
                "error_type": result.error_type,
                "duration_ms": result.duration_ms,
            }
        except Exception as exc:
            logger.exception(
                "[Worker %s] Unexpected error executing task %s",
                self._worker_id, task_dict.get("task_id"),
            )
            trace_manager.finalize("FAILED")
            result_dict = {
                "status": "FAILED",
                "output": None,
                "error": str(exc),
                "error_type": "EXECUTION_ERROR",
                "duration_ms": 0,
            }

        return result_dict, trace_manager.export_dag_trace()

    async def _safe_heartbeat(self) -> None:
        try:
            await self._transport.heartbeat(self._worker_id)
        except Exception as exc:
            logger.warning("[Worker %s] Heartbeat failed: %s", self._worker_id, exc)

    async def _safe_fetch(self) -> dict | None:
        try:
            return await self._transport.fetch_next_task(self._worker_id)
        except Exception as exc:
            logger.warning("[Worker %s] Fetch failed: %s", self._worker_id, exc)
            return None

    async def _safe_submit(self, task_id: str, payload: dict) -> None:
        for attempt in range(1, _MAX_SUBMIT_RETRIES + 1):
            try:
                await self._transport.submit_result(task_id, payload)
                logger.info(
                    "[Worker %s] Submitted result for task=%s status=%s",
                    self._worker_id, task_id, payload.get("status"),
                )
                return
            except Exception as exc:
                logger.warning(
                    "[Worker %s] Submit attempt %d/%d failed for task=%s: %s",
                    self._worker_id, attempt, _MAX_SUBMIT_RETRIES, task_id, exc,
                )
                if attempt < _MAX_SUBMIT_RETRIES:
                    await asyncio.sleep(0.5 * attempt)
        logger.error(
            "[Worker %s] Giving up submitting result for task=%s",
            self._worker_id, task_id,
        )
