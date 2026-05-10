"""freya/experience/translators.py

Runtime event → human-readable progress translation layer.

Uses a registry-based approach (EVENT_TRANSLATIONS dict) to avoid
hardcoded if/else chains. Strategy-aware: the cognitive and recovery
strategies get dedicated human messages distinct from the generic ones.
"""
from __future__ import annotations

from typing import Any

from freya.experience.models import HumanProgressUpdate

# ---------------------------------------------------------------------------
# Configurable event translation registry
# Keys are event_type strings. Values are either a static string or a callable
# that receives the event payload and returns a (title, detail) tuple.
# ---------------------------------------------------------------------------

def _strategy_selected(payload: dict) -> tuple[str, str | None]:
    strategy = payload.get("strategy", "")
    reason = payload.get("reason", "")
    if strategy == "cognitive":
        return "Optimizing travel plan…", "Applying deeper AI reasoning to find the best option."
    if strategy == "recovery":
        return "Retrying with alternate source…", "A temporary issue was detected. Switching data source."
    if strategy == "human_approval":
        return "Waiting for your approval…", None
    if strategy == "delegation":
        return "Coordinating sub-tasks…", None
    return "Processing next step…", reason or None


def _subworkflow_spawned(payload: dict) -> tuple[str, str | None]:
    name = payload.get("child_session_id", "")
    goal = payload.get("goal", "")
    return f"Starting sub-task: {goal or name}", None


EVENT_TRANSLATIONS: dict[str, Any] = {
    # ── Planner lifecycle ─────────────────────────────────────────────────
    "planner_iteration_started":      ("Thinking…", None),
    "planner_iteration_completed":    ("Step complete.", None),
    "planner_terminated":             ("Workflow finished.", None),
    "planner_capabilities_loaded":    ("Tools ready.", None),
    "planner_mode_selected":          ("Planning mode selected.", None),
    "planner_validation_failed":      ("Plan validation failed — retrying…", None),
    "planner_repair_attempted":       ("Attempting to recover plan…", None),
    "planner_repair_succeeded":       ("Plan repaired successfully.", None),
    "planner_repair_failed":          ("Plan repair failed.", None),

    # ── Runtime failures & recovery ───────────────────────────────────────
    "runtime_failure_observed":       ("Encountered a temporary issue.", "Will attempt recovery automatically."),
    "runtime_recovery_attempted":     ("Retrying with alternate source…", None),
    "runtime_recovery_succeeded":     ("Recovery successful. Continuing…", None),
    "runtime_recovery_failed":        ("Recovery attempt failed.", None),
    "runtime_failure_terminal":       ("A critical error ended the workflow.", None),

    # ── Governance ────────────────────────────────────────────────────────
    "governance_evaluated":           None,  # silent — too frequent
    "governance_policy_triggered":    ("Policy check triggered.", None),

    # ── Workflow lifecycle ────────────────────────────────────────────────
    "workflow_paused_for_approval":   ("Waiting for your approval…", "The workflow is paused until you respond."),
    "workflow_resumed_after_approval":("Workflow resumed.", "Continuing after your approval."),
    "workflow_rejected_by_governance":("Workflow rejected.", "The request was declined by governance policy."),
    "workflow_completed":             ("Trip planning complete!", None),
    "workflow_failed":                ("Workflow ended with an error.", None),
    "workflow_snapshot_persisted":    ("Progress saved.", "Your work is safely stored and can be restored."),
    "workflow_snapshot_restored":     ("Progress restored.", "Resuming from your saved checkpoint."),
    "workflow_state_restored":        ("Workflow state restored.", None),
    "workflow_lease_acquired":        None,  # silent
    "workflow_lease_released":        None,  # silent

    # ── Sub-workflows ─────────────────────────────────────────────────────
    "subworkflow_spawned":            _subworkflow_spawned,
    "subworkflow_completed":          ("Sub-task completed.", None),
    "subworkflow_failed":             ("Sub-task failed.", None),

    # ── Delegation ────────────────────────────────────────────────────────
    "delegation_contract_created":    ("Delegating task to specialist…", None),
    "delegation_contract_validated":  ("Delegation validated.", None),
    "delegation_contract_rejected":   ("Delegation rejected.", None),
    "delegation_budget_exceeded":     ("Delegation budget exceeded.", None),

    # ── Strategy ──────────────────────────────────────────────────────────
    "execution_strategy_selected":    _strategy_selected,
    "execution_strategy_escalated":   ("Escalating to stronger reasoning…", None),
    "execution_strategy_blocked":     ("Strategy blocked by budget limit.", None),

    # ── Economics ─────────────────────────────────────────────────────────
    "execution_cost_recorded":        None,  # silent — tracked separately
    "workflow_budget_exceeded":       ("Budget limit reached.", "Please review your workflow budget settings."),
    "high_cost_workflow_detected":    ("High-cost workflow detected.", None),
}

# Tool-name → human label for tool_call events emitted by the DAG runner
TOOL_LABELS: dict[str, str] = {
    "search_primary_flights":      "Searching flights…",
    "search_alternative_flights":  "Searching alternate flights…",
    "search_hotels":               "Finding available hotels…",
    "compare_hotels":              "Comparing hotel options…",
    "build_itinerary":             "Building your meeting itinerary…",
    "estimate_costs":              "Calculating trip costs…",
}


class RuntimeEventTranslator:
    """Translates RuntimeEvents (or raw event dicts) into HumanProgressUpdates.

    Filters verbosity, suppresses internal-only events, and maps
    runtime terminology to human language using the registry above.
    """

    def __init__(self, extra_translations: dict[str, Any] | None = None) -> None:
        self._registry: dict[str, Any] = {**EVENT_TRANSLATIONS}
        if extra_translations:
            self._registry.update(extra_translations)

    def translate(self, event: dict) -> HumanProgressUpdate | None:
        """Return a HumanProgressUpdate or None if the event should be silent."""
        event_type: str = event.get("event_type", "")
        payload: dict = event.get("payload", {})

        # Check direct tool-call events embedded in payload
        if event_type in ("tool_call_started", "tool_call_completed"):
            tool_name = payload.get("tool_name", "")
            label = TOOL_LABELS.get(tool_name)
            if label:
                status = "done" if event_type == "tool_call_completed" else "running"
                return HumanProgressUpdate(title=label, status=status)
            return None

        entry = self._registry.get(event_type)

        # Explicitly silenced
        if entry is None and event_type in self._registry:
            return None
        if entry is None:
            return None  # unknown events are silent by default

        # Callable → dynamic translation
        if callable(entry):
            result = entry(payload)
            if result is None:
                return None
            title, detail = result
        else:
            title, detail = entry

        # Map event type to status
        status = _classify_status(event_type, payload)

        return HumanProgressUpdate(title=title, status=status, detail=detail)

    def translate_all(self, events: list[dict]) -> list[HumanProgressUpdate]:
        """Translate a list of events, dropping silent ones."""
        updates: list[HumanProgressUpdate] = []
        for ev in events:
            update = self.translate(ev)
            if update is not None:
                updates.append(update)
        return updates


def _classify_status(event_type: str, payload: dict) -> str:
    if event_type in ("workflow_completed", "runtime_recovery_succeeded",
                       "planner_repair_succeeded", "subworkflow_completed"):
        return "done"
    if event_type in ("workflow_failed", "runtime_failure_terminal",
                       "delegation_contract_rejected", "workflow_rejected_by_governance"):
        return "failed"
    if event_type in ("workflow_paused_for_approval",):
        return "paused"
    if event_type in ("runtime_failure_observed", "workflow_budget_exceeded",
                       "high_cost_workflow_detected", "planner_validation_failed"):
        return "warning"
    if event_type in ("execution_strategy_selected",):
        strategy = payload.get("strategy", "")
        if strategy in ("recovery", "human_approval"):
            return "warning"
        return "running"
    return "running"
