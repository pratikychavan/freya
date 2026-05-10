"""freya/experience/progress.py

Tracks workflow progress steps and renders them as a clean human-
readable checklist. Deduplicates repeated events and collapses
noisy intermediate iterations into meaningful milestones.
"""
from __future__ import annotations

from datetime import datetime, timezone

from freya.experience.models import HumanProgressUpdate, SessionContinuityUpdate
from freya.experience.translators import RuntimeEventTranslator

# ---------------------------------------------------------------------------
# Milestone steps — fixed ordered list that maps to tool completions
# ---------------------------------------------------------------------------

PROGRESS_STEPS: list[tuple[str, str]] = [
    # (completed_task_id or sentinel, human label)
    ("search_primary_flights|search_alternative_flights", "Searching for flights"),
    ("search_hotels",                                      "Finding available hotels"),
    ("compare_hotels",                                     "Comparing hotel options"),
    ("build_itinerary",                                    "Building meeting itinerary"),
    ("estimate_costs",                                     "Calculating trip costs"),
]


class WorkflowProgressTracker:
    """Builds a human-readable progress checklist from completed task IDs.

    Instantiate once, call ``update()`` as tasks complete, then call
    ``render()`` to get the current checklist string.
    """

    def __init__(self) -> None:
        self._completed: set[str] = set()
        self._failed: set[str] = set()
        self._current: str | None = None  # currently running step label
        self._continuity: list[SessionContinuityUpdate] = []

    def mark_completed(self, task_id: str) -> None:
        self._completed.add(task_id)

    def mark_failed(self, task_id: str) -> None:
        self._failed.add(task_id)

    def set_current(self, task_id: str) -> None:
        self._current = task_id

    def add_continuity(self, message: str, state: str) -> None:
        self._continuity.append(
            SessionContinuityUpdate(message=message, state=state)
        )

    def from_completed_tasks(self, completed_tasks: list[str]) -> "WorkflowProgressTracker":
        """Populate completed tasks from the final context."""
        for task_id in completed_tasks:
            self.mark_completed(task_id)
        return self

    def from_events(self, events: list[dict]) -> "WorkflowProgressTracker":
        """Populate tracker state from a list of raw event dicts."""
        seen_continuity: set[str] = set()

        def _add(message: str, state: str) -> None:
            key = f"{state}:{message}"
            if key not in seen_continuity:
                seen_continuity.add(key)
                self.add_continuity(message, state)
        for ev in events:
            etype = ev.get("event_type", "")
            payload = ev.get("payload", {})

            if etype == "tool_call_completed":
                tool = payload.get("tool_name", "")
                if tool:
                    self.mark_completed(tool)

            if etype in ("workflow_snapshot_persisted",):
                _add("Progress saved.", "paused")
            if etype in ("workflow_snapshot_restored",):
                _add("Resuming from saved checkpoint.", "restored")
            if etype == "workflow_paused_for_approval":
                _add("Trip planning paused — awaiting your approval.", "paused")
            if etype == "workflow_resumed_after_approval":
                _add("Trip planning resumed after your approval.", "resumed")
            if etype == "workflow_completed":
                _add("Trip planning completed successfully.", "completed")
            if etype in ("workflow_failed", "runtime_failure_terminal"):
                _add("Planning ended with an error.", "failed")

        return self

    def render(self) -> str:
        """Render the progress checklist as a terminal-friendly string."""
        lines: list[str] = []

        for task_ids_str, label in PROGRESS_STEPS:
            task_ids = task_ids_str.split("|")
            if any(tid in self._completed for tid in task_ids):
                lines.append(f"  ✓  {label}")
            elif any(tid in self._failed for tid in task_ids):
                lines.append(f"  ✗  {label}")
            else:
                lines.append(f"  ○  {label}")

        return "\n".join(lines)

    def render_continuity(self) -> str:
        """Render session continuity messages."""
        if not self._continuity:
            return ""
        return "\n".join(c.render() for c in self._continuity)


def build_progress_from_events(events: list[dict]) -> WorkflowProgressTracker:
    """Convenience factory: build a tracker directly from event list."""
    tracker = WorkflowProgressTracker()
    tracker.from_events(events)
    return tracker
