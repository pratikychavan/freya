from __future__ import annotations

import logging
from collections import deque
from typing import TYPE_CHECKING

from freya.events.models import EventType, RuntimeEvent

if TYPE_CHECKING:
    from freya.events.base import EventSubscriber

logger = logging.getLogger(__name__)

_DEFAULT_REPLAY_CAPACITY = 200


class InProcessEventBus:
    """Single-process async event bus with fan-out and subscriber failure isolation.

    Features:
    - Sequential subscriber dispatch (deterministic ordering).
    - Subscriber exceptions never crash the runtime; they produce a
      ``subscriber_failure`` event that all *other* subscribers receive.
    - Optional in-memory replay buffer (last N events).

    Usage::

        bus = InProcessEventBus()
        bus.subscribe(MySubscriber())
        await bus.publish(RuntimeEvent(event_type="foo", session_id="s1"))
    """

    def __init__(self, replay_capacity: int = _DEFAULT_REPLAY_CAPACITY) -> None:
        self._subscribers: list[EventSubscriber] = []
        self._replay: deque[RuntimeEvent] = deque(maxlen=replay_capacity)

    # ------------------------------------------------------------------
    # Subscriber management
    # ------------------------------------------------------------------

    def subscribe(self, subscriber: "EventSubscriber") -> None:
        """Register a subscriber. Subscribers are invoked in registration order."""
        self._subscribers.append(subscriber)

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    async def publish(self, event: RuntimeEvent) -> None:
        """Fan-out *event* to all registered subscribers.

        Each subscriber is called sequentially.  If a subscriber raises an
        exception the failure is captured, a ``subscriber_failure`` event is
        published to the *remaining* subscribers, and dispatching continues.
        The replay buffer receives the original event regardless of failures.
        """
        self._replay.append(event)

        subscribers = list(self._subscribers)  # snapshot to avoid mutation mid-loop
        for idx, subscriber in enumerate(subscribers):
            try:
                await subscriber.handle_event(event)
            except Exception as exc:
                name = type(subscriber).__name__
                logger.warning(
                    "EventBus: subscriber %r raised during %r: %s",
                    name,
                    event.event_type,
                    exc,
                )
                failure_event = RuntimeEvent(
                    event_type=EventType.SUBSCRIBER_FAILURE,
                    session_id=event.session_id,
                    iteration=event.iteration,
                    payload={
                        "subscriber_name": name,
                        "failed_event_type": event.event_type,
                        "error": str(exc),
                    },
                )
                self._replay.append(failure_event)
                # Notify remaining subscribers (skip failed one to avoid re-entry).
                for other in subscribers[idx + 1 :]:
                    try:
                        await other.handle_event(failure_event)
                    except Exception:
                        pass  # Secondary failures are swallowed.

    # ------------------------------------------------------------------
    # Replay buffer
    # ------------------------------------------------------------------

    def recent_events(self, limit: int = 50) -> list[RuntimeEvent]:
        """Return the most recent *limit* events from the replay buffer."""
        all_events = list(self._replay)
        return all_events[-limit:]

    def clear_replay(self) -> None:
        """Clear the replay buffer (useful between test scenarios)."""
        self._replay.clear()
