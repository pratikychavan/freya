from __future__ import annotations

from abc import ABC, abstractmethod


class ControlPlaneTransport(ABC):
    """Abstract transport for interacting with a control plane."""

    @abstractmethod
    async def fetch_next_task(self, worker_id: str) -> dict | None:
        """Return the next task dict or None if the queue is empty."""
        ...

    @abstractmethod
    async def submit_result(self, task_id: str, result: dict) -> None:
        """Send execution result back to the control plane."""
        ...

    @abstractmethod
    async def heartbeat(self, worker_id: str) -> None:
        """Notify the control plane that this worker is alive."""
        ...
