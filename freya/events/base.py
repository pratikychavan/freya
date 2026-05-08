from __future__ import annotations

from typing import Protocol, runtime_checkable

from freya.events.models import RuntimeEvent


@runtime_checkable
class EventSubscriber(Protocol):
    """Protocol for all runtime event subscribers.

    Subscribers MUST:
    - never mutate runtime state directly
    - never block indefinitely
    - remain side-effect isolated

    Subscriber exceptions are caught by the bus and do NOT crash the runtime.
    """

    async def handle_event(self, event: RuntimeEvent) -> None:
        """Process a single runtime event."""
        ...
