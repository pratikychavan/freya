from __future__ import annotations

import logging

from freya.events.models import EventType, RuntimeEvent
from freya.governance.state import WorkflowState

logger = logging.getLogger(__name__)


class TraceSubscriber:
    """Converts RuntimeEvents into a structured in-memory audit log.

    Records every event in arrival order.  Suitable for debugging and
    post-run inspection.
    """

    def __init__(self) -> None:
        self._entries: list[dict] = []

    async def handle_event(self, event: RuntimeEvent) -> None:
        self._entries.append({
            "event_type": event.event_type,
            "session_id": event.session_id,
            "iteration": event.iteration,
            "timestamp": event.timestamp.isoformat(),
            "payload": event.payload,
        })

    @property
    def entries(self) -> list[dict]:
        return list(self._entries)

    def entries_for_session(self, session_id: str) -> list[dict]:
        return [e for e in self._entries if e["session_id"] == session_id]


class PersistenceSubscriber:
    """Automatically persists workflow snapshots on lifecycle transitions.

    Triggers a snapshot write when a workflow:
    - pauses for approval
    - resumes after approval
    - completes
    - fails

    Requires a :class:`~freya.governance.persistent_store.PersistentWorkflowStore`
    and optionally a snapshot builder callback.
    """

    def __init__(
        self,
        persistent_store: object,  # PersistentWorkflowStore — avoid circular import
        snapshot_builder: object | None = None,
    ) -> None:
        self._store = persistent_store
        self._snapshot_builder = snapshot_builder
        self._persisted: list[str] = []  # session_ids that were written

    _TRIGGER_EVENT_TYPES = {
        EventType.WORKFLOW_PAUSED_FOR_APPROVAL,
        EventType.WORKFLOW_RESUMED_AFTER_APPROVAL,
        EventType.WORKFLOW_COMPLETED,
        EventType.WORKFLOW_FAILED,
    }

    async def handle_event(self, event: RuntimeEvent) -> None:
        if event.event_type not in self._TRIGGER_EVENT_TYPES:
            return
        if self._snapshot_builder is None:
            return

        try:
            snapshot = self._snapshot_builder(event)
            if snapshot is not None:
                self._store.save_snapshot(snapshot)  # type: ignore[attr-defined]
                self._persisted.append(event.session_id)
        except Exception as exc:
            logger.warning(
                "PersistenceSubscriber: failed to persist snapshot for session %r: %s",
                event.session_id,
                exc,
            )

    @property
    def persisted_sessions(self) -> list[str]:
        return list(self._persisted)


class GovernanceAuditSubscriber:
    """Records all governance-related lifecycle events for audit purposes.

    Maintains an ordered log of governance decisions, policy triggers,
    approval requests, and rejection events — suitable for compliance
    auditing and debugging.
    """

    def __init__(self) -> None:
        self._audit_log: list[dict] = []

    _GOVERNANCE_EVENT_TYPES = {
        EventType.GOVERNANCE_EVALUATED,
        EventType.GOVERNANCE_POLICY_TRIGGERED,
        EventType.WORKFLOW_PAUSED_FOR_APPROVAL,
        EventType.WORKFLOW_RESUMED_AFTER_APPROVAL,
        EventType.WORKFLOW_REJECTED_BY_GOVERNANCE,
        EventType.WORKFLOW_RESUME_REJECTED,
        EventType.WORKFLOW_LEASE_ACQUIRED,
        EventType.WORKFLOW_LEASE_RELEASED,
        EventType.WORKFLOW_VERSION_CONFLICT,
    }

    async def handle_event(self, event: RuntimeEvent) -> None:
        if event.event_type not in self._GOVERNANCE_EVENT_TYPES:
            return
        self._audit_log.append({
            "event_type": event.event_type,
            "session_id": event.session_id,
            "iteration": event.iteration,
            "timestamp": event.timestamp.isoformat(),
            "payload": event.payload,
        })

    @property
    def audit_log(self) -> list[dict]:
        return list(self._audit_log)

    def log_for_session(self, session_id: str) -> list[dict]:
        return [e for e in self._audit_log if e["session_id"] == session_id]
