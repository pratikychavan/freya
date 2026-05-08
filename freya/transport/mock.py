from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import Any

from freya.transport.base import ControlPlaneTransport

logger = logging.getLogger(__name__)


class MockTransport(ControlPlaneTransport):
    """In-memory transport for testing — push tasks in, pull results out."""

    def __init__(self) -> None:
        self._queue: deque[dict] = deque()
        self._results: dict[str, dict] = {}
        self._heartbeats: list[str] = []

    # ------------------------------------------------------------------
    # Control-plane-side helpers (test/example use)
    # ------------------------------------------------------------------

    def push_task(self, task: dict) -> None:
        """Enqueue a task for the worker to pick up."""
        self._queue.append(task)

    def get_result(self, task_id: str) -> dict | None:
        return self._results.get(task_id)

    def all_results(self) -> dict[str, dict]:
        return dict(self._results)

    # ------------------------------------------------------------------
    # ControlPlaneTransport interface
    # ------------------------------------------------------------------

    async def fetch_next_task(self, worker_id: str) -> dict | None:
        if self._queue:
            task = self._queue.popleft()
            logger.debug("MockTransport: worker=%s fetched task=%s", worker_id, task.get("task_id"))
            return task
        return None

    async def submit_result(self, task_id: str, result: dict) -> None:
        self._results[task_id] = result
        logger.debug("MockTransport: stored result for task=%s status=%s", task_id, result.get("status"))

    async def heartbeat(self, worker_id: str) -> None:
        self._heartbeats.append(worker_id)
        logger.debug("MockTransport: heartbeat from worker=%s", worker_id)
