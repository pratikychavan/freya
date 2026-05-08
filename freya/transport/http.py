from __future__ import annotations

import logging
from typing import Any

import httpx

from freya.transport.base import ControlPlaneTransport

logger = logging.getLogger(__name__)


class HttpTransport(ControlPlaneTransport):
    """HTTP transport implementation using httpx (async)."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def fetch_next_task(self, worker_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{self._base_url}/tasks/next",
                params={"worker_id": worker_id},
            )
            if resp.status_code == 204:
                return None
            resp.raise_for_status()
            return resp.json()

    async def submit_result(self, task_id: str, result: dict) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/tasks/{task_id}/result",
                json=result,
            )
            resp.raise_for_status()

    async def heartbeat(self, worker_id: str) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/workers/{worker_id}/heartbeat"
            )
            resp.raise_for_status()
