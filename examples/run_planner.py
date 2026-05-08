"""
Iterative Planner example — Resilient Governed Cognition with HITL Checkpoints
================================================================================
Demonstrates observation-aware, resilient, governed planning with
validation + repair, runtime recovery, governance evaluation,
approval checkpoints (workflow pausing and resuming),
durable workflow persistence (crash-safe resume across process restarts),
and concurrency-safe workflow versioning with execution leases.

Scenarios:

  A. DETERMINISTIC  — observation-driven, happy path
  B. COGNITIVE      — uses explain_number prompt capability
  C. SUCCESSFUL REPAIR — planner first produces a bad tool name,
                         validator rejects it, planner repairs → success
  D. FAILED REPAIR  — planner produces an invalid DAG twice,
                       runner terminates safely
  E. RECOVERABLE RUNTIME FAILURE — FlakyTool times out → retry → success
  F. UNRECOVERABLE RUNTIME FAILURE — FatalTool → safe termination
  G. GOVERNANCE APPROVE  — deterministic, no dangerous tools → APPROVE
  H. GOVERNANCE REQUIRE_APPROVAL (cognitive) — COGNITIVE mode → REQUIRE_APPROVAL
  I. GOVERNANCE REQUIRE_APPROVAL (dangerous tool) — write_value flagged
  J. APPROVAL REQUIRED — cognitive workflow pauses for HITL approval
  K. APPROVED RESUME   — approve the paused request → execution completes
  L. REJECTED WORKFLOW — reject the paused request → safe termination
  M. DURABLE PAUSE     — workflow pauses and snapshot is written to disk
  N. SIMULATED RESTART — destroy runner, reconstruct from snapshot on disk
  O. RESUME AFTER RESTART — approve on disk, resume on new runner → completes
  P. LEASE ACQUISITION   — runner A acquires workflow lease; trace emitted
  Q. CONCURRENT RESUME REJECTED — runner B blocked by runner A's lease
  R. STALE SNAPSHOT WRITE — outdated save raises WorkflowVersionConflictError
  S. SUCCESSFUL RESUME AFTER LEASE TRANSFER — lease released; runner B resumes
  T. EVENT STREAM        — print ordered runtime events from InProcessEventBus
  U. SUBSCRIBER FAILURE ISOLATION — crashing subscriber; workflow still completes
  V. PERSISTENCE SUBSCRIBER — snapshot auto-persisted via event bus
  W. SUBWORKFLOW DELEGATION — parent spawns child; child completes; parent continues
  X. CHILD FAILURE OBSERVATION — child fails; parent observes summarized failure
  Y. WORKFLOW TREE        — render workflow hierarchy
  Z. GOVERNANCE INHERITED — child pauses for approval independently
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from freya import (
    DAGRunner,
    ExecutionEngine,
    ExecutionContext,
    InMemoryStore,
    Prompt,
    PromptRegistry,
    PromptCapabilityRegistry,
    PromptCapability,
    ToolRegistry,
    Tool,
    IterativePlannerRunner,
    SimpleIterativePlanner,
    PlanningMode,
    GovernanceEngine,
    CognitiveModeApprovalPolicy,
    DangerousToolPolicy,
    ExcessiveRecoveryPolicy,
    InMemoryApprovalStore,
    WorkflowState,
    PersistentWorkflowStore,
    WorkflowVersionConflictError,
    WorkflowLeaseError,
    WorkflowAlreadyResumedError,
    RuntimeEvent,
    EventType,
    InProcessEventBus,
    TraceSubscriber,
    PersistenceSubscriber,
    GovernanceAuditSubscriber,
)
from freya import (
    WorkflowCoordinator,
    WorkflowRelationship,
    RelationshipType,
    render_workflow_tree,
)


# ---------------------------------------------------------------------------
# Simple memory R/W tools  (created only for this example)
# ---------------------------------------------------------------------------

class _WriteInput(BaseModel):
    key: str
    value: Any


class _WriteOutput(BaseModel):
    written_key: str
    written_value: Any


class WriteValueTool(Tool):
    """Write a value to session memory under the given key."""

    name = "write_value"
    input_model = _WriteInput
    output_model = _WriteOutput

    async def execute(self, input: _WriteInput, context: ExecutionContext) -> _WriteOutput:  # type: ignore[override]
        context.memory.set(context.session_id, input.key, input.value)
        return _WriteOutput(written_key=input.key, written_value=input.value)


class _ReadInput(BaseModel):
    key: str


class _ReadOutput(BaseModel):
    key: str
    value: Any


class ReadValueTool(Tool):
    """Read a value from session memory by key."""

    name = "read_value"
    input_model = _ReadInput
    output_model = _ReadOutput

    async def execute(self, input: _ReadInput, context: ExecutionContext) -> _ReadOutput:  # type: ignore[override]
        value = context.memory.get(context.session_id, input.key)
        return _ReadOutput(key=input.key, value=value)


class FlakyTool(Tool):
    """Fails on the first call per session key, succeeds on subsequent calls."""

    name = "flaky_store"
    input_model = _WriteInput
    output_model = _WriteOutput

    async def execute(self, input: _WriteInput, context: ExecutionContext) -> _WriteOutput:  # type: ignore[override]
        count_key = f"_flaky_count_{input.key}"
        call_count = context.memory.get(context.session_id, count_key) or 0
        context.memory.set(context.session_id, count_key, call_count + 1)
        if call_count == 0:
            raise TimeoutError(f"flaky_store: connection timed out storing key '{input.key}'")
        return _WriteOutput(written_key=input.key, written_value=input.value)


class FatalTool(Tool):
    """Always raises an unrecoverable exception."""

    name = "fatal_operation"
    input_model = _WriteInput
    output_model = _WriteOutput

    async def execute(self, input: _WriteInput, context: ExecutionContext) -> _WriteOutput:  # type: ignore[override]
        raise RuntimeError("FATAL_UNRECOVERABLE: operation not supported by backend")


# ---------------------------------------------------------------------------
# Build registries
# ---------------------------------------------------------------------------

def _build_tool_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(WriteValueTool())
    reg.register(ReadValueTool())
    return reg


def _build_recovery_tool_registry() -> ToolRegistry:
    """Registry for runtime recovery scenarios — includes flaky and fatal tools."""
    reg = ToolRegistry()
    reg.register(WriteValueTool())
    reg.register(ReadValueTool())
    reg.register(FlakyTool())
    reg.register(FatalTool())
    return reg


def _build_prompt_registry() -> PromptRegistry:
    pr = PromptRegistry()

    # Observation-aware planner prompt — no {iteration} variable.
    # The planner decides what to do next based on recent_observations.
    pr.register(
        "plan_next",
        Prompt(
            template=(
                "Goal: {goal}\n\n"
                "Recent observations (what has happened so far):\n{recent_observations}\n\n"
                "Memory summary: {memory_summary}\n\n"
                "Completed tasks: {completed_tasks}\n"
                "Failed tasks: {failed_tasks}\n\n"
                "Available tools:\n{available_tools}\n"
                "{available_prompt_capabilities}"
                "\nBased on the observations above, return the NEXT DAG fragment as JSON "
                "with a 'tasks' array, or an empty tasks array when the goal is complete."
            ),
            system=(
                "You are an observation-driven planning assistant. "
                "Determine the next step purely from what has been observed. "
                "Return only valid JSON."
            ),
        ),
    )

    # Execution-time prompt for the explanation step (cognitive mode only)
    pr.register(
        "explain_number",
        Prompt(
            template="The retrieved value is: {value}\n\nExplain this value in one sentence.",
            system="You are a concise assistant.",
        ),
    )

    return pr


def _build_prompt_capability_registry() -> PromptCapabilityRegistry:
    """Register all available reasoning operations for cognitive-mode planning."""
    pcr = PromptCapabilityRegistry()

    pcr.register(PromptCapability(
        name="explain_number",
        purpose="explanation",
        description="Explain a numeric value in plain language.",
        required_inputs=["value"],
        output_description="A one-sentence human-readable explanation.",
        planning_mode=PlanningMode.COGNITIVE,
    ))
    pcr.register(PromptCapability(
        name="summarize_logs",
        purpose="log_analysis",
        description="Summarise a block of log text and highlight important failures.",
        required_inputs=["log_text"],
        output_description="A summary of important failures found in the logs.",
        planning_mode=PlanningMode.COGNITIVE,
    ))
    pcr.register(PromptCapability(
        name="classify_error",
        purpose="error_classification",
        description="Classify an error message into a structured category.",
        required_inputs=["error_message"],
        output_description="An error category label with a one-line description.",
        planning_mode=PlanningMode.COGNITIVE,
    ))

    return pcr


# ---------------------------------------------------------------------------
# Scripted planner LLMs — responses driven by what observations say
# ---------------------------------------------------------------------------

def _make_deterministic_planner_llm() -> AsyncMock:
    """
    DETERMINISTIC mode.
    The mock simulates a planner that:
      - observes nothing yet → writes 10
      - observes store_value succeeded → reads it back
      - observes retrieve_value succeeded with value=10 → signals done
    """
    llm = AsyncMock()
    llm.complete.side_effect = [
        # Observation: no prior observations → first step: write
        {"text": json.dumps({"tasks": [{"task_id": "store_value", "type": "tool", "input": {"tool_name": "write_value", "tool_input": {"key": "my_number", "value": 10}}}]}), "usage": {}},
        # Observation: store_value succeeded → read it back
        {"text": json.dumps({"tasks": [{"task_id": "retrieve_value", "type": "tool", "input": {"tool_name": "read_value", "tool_input": {"key": "my_number"}}}]}), "usage": {}},
        # Observation: retrieve_value succeeded → goal complete, terminate
        {"text": json.dumps({"tasks": []}), "usage": {}},
    ]
    return llm


def _make_cognitive_planner_llm() -> AsyncMock:
    """
    COGNITIVE mode.
    The mock simulates a planner that:
      - observes nothing yet → writes 10
      - observes store_value succeeded → reads it back
      - observes retrieve_value succeeded with value=10
        AND explain_number capability is available → explain the value
      - observes explain_value succeeded → signals done
    """
    llm = AsyncMock()
    llm.complete.side_effect = [
        # No observations yet → write
        {"text": json.dumps({"tasks": [{"task_id": "store_value", "type": "tool", "input": {"tool_name": "write_value", "tool_input": {"key": "my_number", "value": 10}}}]}), "usage": {}},
        # store_value observed → read
        {"text": json.dumps({"tasks": [{"task_id": "retrieve_value", "type": "tool", "input": {"tool_name": "read_value", "tool_input": {"key": "my_number"}}}]}), "usage": {}},
        # retrieve_value observed with value=10 + explain_number capability visible → explain
        {"text": json.dumps({"tasks": [{"task_id": "explain_value", "type": "llm", "input": {"prompt_name": "explain_number", "variables": {"value": "10"}, "model": "gpt-4o-mini"}}]}), "usage": {}},
        # explain_value observed → done
        {"text": json.dumps({"tasks": []}), "usage": {}},
    ]
    return llm


def _make_repair_success_planner_llm() -> AsyncMock:
    """Scenario C: first call uses bad tool name 'write_values'; repair fixes it."""
    llm = AsyncMock()
    llm.complete.side_effect = [
        # Initial plan — invalid tool name
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "store_value",
                    "type": "tool",
                    "input": {"tool_name": "write_values", "tool_input": {"key": "my_number", "value": 10}},
                }]
            }),
            "usage": {},
        },
        # Repair response — correct tool name
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "store_value",
                    "type": "tool",
                    "input": {"tool_name": "write_value", "tool_input": {"key": "my_number", "value": 10}},
                }]
            }),
            "usage": {},
        },
        # Next iteration — read
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "retrieve_value",
                    "type": "tool",
                    "input": {"tool_name": "read_value", "tool_input": {"key": "my_number"}},
                }]
            }),
            "usage": {},
        },
        # Done
        {"text": json.dumps({"tasks": []}), "usage": {}},
    ]
    return llm


def _make_repair_fail_planner_llm() -> AsyncMock:
    """Scenario D: both initial and repair calls reference nonexistent tools → safe termination."""
    llm = AsyncMock()
    llm.complete.side_effect = [
        # Initial plan — nonexistent tool
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "bad_task",
                    "type": "tool",
                    "input": {"tool_name": "nonexistent_tool", "tool_input": {}},
                }]
            }),
            "usage": {},
        },
        # Repair response — still invalid
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "bad_task",
                    "type": "tool",
                    "input": {"tool_name": "also_nonexistent", "tool_input": {}},
                }]
            }),
            "usage": {},
        },
    ]
    return llm


def _make_recovery_success_planner_llm() -> AsyncMock:
    """Scenario E: FlakyTool times out → planner retries → success → done."""
    llm = AsyncMock()
    llm.complete.side_effect = [
        # plan_next iter=0 — use the flaky tool
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "flaky_store",
                    "type": "tool",
                    "input": {"tool_name": "flaky_store", "tool_input": {"key": "num", "value": 42}},
                }]
            }),
            "usage": {},
        },
        # plan_recovery — retry the same task (flaky tool succeeds on 2nd call)
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "flaky_store",
                    "type": "tool",
                    "input": {"tool_name": "flaky_store", "tool_input": {"key": "num", "value": 42}},
                }]
            }),
            "usage": {},
        },
        # plan_next iter=1 — recovery observed as success → done
        {"text": json.dumps({"tasks": []}), "usage": {}},
    ]
    return llm


def _make_recovery_fatal_planner_llm() -> AsyncMock:
    """Scenario F: FatalTool raises unrecoverable error → safe termination."""
    llm = AsyncMock()
    llm.complete.side_effect = [
        # plan_next iter=0 — use the fatal tool
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "fatal_op",
                    "type": "tool",
                    "input": {"tool_name": "fatal_operation", "tool_input": {"key": "x", "value": 0}},
                }]
            }),
            "usage": {},
        },
    ]
    return llm


def _make_post_restore_planner_llm() -> AsyncMock:
    """Scenarios N/O: after workflow restoration, planner signals done immediately.

    The paused DAG (from the snapshot) is executed first by
    resume_from_approval(), then the planning loop calls plan_next once.
    Returning an empty DAG here means the workflow completes straight after
    the restored task runs — no new governance pause is triggered.
    """
    llm = AsyncMock()
    llm.complete.side_effect = [
        {"text": json.dumps({"tasks": []}), "usage": {}},
    ]
    return llm


def _make_dangerous_tool_planner_llm() -> AsyncMock:
    """Scenario I: DAG references delete_data → DangerousToolPolicy fires → REQUIRE_APPROVAL."""
    llm = AsyncMock()
    llm.complete.side_effect = [
        # Iteration 0 — use dangerous tool
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "wipe_records",
                    "type": "tool",
                    "input": {"tool_name": "write_value", "tool_input": {"key": "x", "value": 1}},
                }]
            }),
            "usage": {},
        },
        # Done
        {"text": json.dumps({"tasks": []}), "usage": {}},
    ]
    return llm


def _make_hitl_demo_planner_llm() -> AsyncMock:
    """Scenarios J/K/L: one fragment that triggers governance pause, then done.

    Call 0 → store_value DAG (paused by CognitiveModeApprovalPolicy)
    Call 1 → empty DAG (signals completion after approval in scenario K)

    For scenario L (rejection), call 1 is never reached because resume
    terminates immediately on REJECTED state.
    """
    llm = AsyncMock()
    llm.complete.side_effect = [
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "store_value",
                    "type": "tool",
                    "input": {"tool_name": "write_value", "tool_input": {"key": "hitl_key", "value": 42}},
                }]
            }),
            "usage": {},
        },
        # After resumed approval: planner signals done.
        {"text": json.dumps({"tasks": []}), "usage": {}},
    ]
    return llm


def _make_subworkflow_w_planner_llm() -> AsyncMock:
    """Scenario W: parent spawns child subworkflow; both complete.

    Call 0 (parent iter=0): return subworkflow DAG
    Call 1 (child iter=0):  return write_value tool task
    Call 2 (child iter=1):  empty DAG (child done)
    Call 3 (parent iter=1): empty DAG (parent done)
    """
    llm = AsyncMock()
    llm.complete.side_effect = [
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "analyze_logs",
                    "type": "subworkflow",
                    "input": {"goal": "Analyze log data and store result", "planning_mode": "deterministic"},
                }]
            }),
            "usage": {},
        },
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "store_log_result",
                    "type": "tool",
                    "input": {"tool_name": "write_value", "tool_input": {"key": "log_result", "value": "logs_are_clean"}},
                }]
            }),
            "usage": {},
        },
        {"text": json.dumps({"tasks": []}), "usage": {}},
        {"text": json.dumps({"tasks": []}), "usage": {}},
    ]
    return llm


def _make_subworkflow_x_planner_llm() -> AsyncMock:
    """Scenario X: child workflow fails; parent observes and adapts.

    Call 0 (parent iter=0): return subworkflow DAG
    Call 1 (child iter=0):  return fatal_operation (child fails)
    Call 2 (parent iter=1): empty DAG (parent adapts after observing failure)
    """
    llm = AsyncMock()
    llm.complete.side_effect = [
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "classify_incident",
                    "type": "subworkflow",
                    "input": {"goal": "Classify security incident"},
                }]
            }),
            "usage": {},
        },
        {
            "text": json.dumps({
                "tasks": [{
                    "task_id": "run_classifier",
                    "type": "tool",
                    "input": {"tool_name": "fatal_operation", "tool_input": {"key": "x", "value": 0}},
                }]
            }),
            "usage": {},
        },
        {"text": json.dumps({"tasks": []}), "usage": {}},
    ]
    return llm


def _make_execution_llm() -> AsyncMock:
    llm = AsyncMock()
    llm.complete.return_value = {
        "text": (
            "The value 10 is a positive integer that was stored in memory "
            "and successfully retrieved, confirming the session store is working correctly."
        ),
        "usage": {"prompt_tokens": 20, "completion_tokens": 28, "total_tokens": 48},
    }
    return llm


# ---------------------------------------------------------------------------
# Governance engine builders
# ---------------------------------------------------------------------------

def _build_standard_governance() -> GovernanceEngine:
    """All three standard policies."""
    ge = GovernanceEngine()
    ge.register(CognitiveModeApprovalPolicy())
    ge.register(DangerousToolPolicy())
    ge.register(ExcessiveRecoveryPolicy(threshold=1))
    return ge


def _build_dangerous_tool_governance() -> GovernanceEngine:
    """DangerousToolPolicy that also considers write_value dangerous for demo purposes."""
    ge = GovernanceEngine()
    ge.register(DangerousToolPolicy(dangerous_tools=frozenset({"delete_data", "write_value"})))
    return ge


# ---------------------------------------------------------------------------
# Print helper
# ---------------------------------------------------------------------------

def _print_result(result: object) -> None:
    from freya import PlannerResult  # type: ignore
    r: PlannerResult = result  # type: ignore
    print(f"\nPlanning mode      : {r.final_context.planning_mode.value}")
    print(f"Status             : {r.trace.status}")
    print(f"Termination reason : {r.trace.termination_reason}")
    print(f"Iterations run     : {r.trace.iterations_completed}")
    print(f"Completed tasks    : {r.final_context.completed_tasks}")
    print(f"Failed tasks       : {r.final_context.failed_tasks or '(none)'}")

    print("\n--- Tool capabilities seen by planner ---")
    for cap in r.final_context.available_tools:
        print(f"  {cap.name}  —  {cap.description}")

    if r.final_context.available_prompt_capabilities:
        print("\n--- Prompt capabilities seen by planner (cognitive only) ---")
        for cap in r.final_context.available_prompt_capabilities:
            print(f"  {cap.name}  —  purpose={cap.purpose}  inputs={cap.required_inputs}")
    else:
        print("\n--- Prompt capabilities seen by planner ---")
        print("  (none — deterministic mode)")

    print("\n--- Observation summaries ---")
    for obs in r.final_context.recent_observations:
        print(f"  {obs.as_summary()}")

    print("\n--- Task outputs ---")
    for task_id, info in r.final_context.task_results.items():
        status = info["status"]
        output = json.dumps(info["output"])[:80] if info["output"] else info["error"]
        icon = "✓" if status == "SUCCESS" else "✗"
        print(f"  [{icon}] {task_id:<20}  {output}")

    repair_events = {"planner_validation_failed", "planner_repair_attempted",
                     "planner_repair_succeeded", "planner_repair_failed"}
    repair_trace = [ev for ev in r.trace.events if ev.event_type in repair_events]
    if repair_trace:
        print("\n--- Repair trace events ---")
        for ev in repair_trace:
            print(f"  iter={ev.iteration}  {ev.event_type:<40}  {ev.payload}")

    recovery_events = {"runtime_failure_observed", "runtime_recovery_attempted",
                       "runtime_recovery_succeeded", "runtime_recovery_failed",
                       "runtime_failure_terminal"}
    recovery_trace = [ev for ev in r.trace.events if ev.event_type in recovery_events]
    if recovery_trace:
        print("\n--- Runtime recovery trace events ---")
        for ev in recovery_trace:
            print(f"  iter={ev.iteration}  {ev.event_type:<40}  {ev.payload}")

    governance_events = {"governance_evaluated", "governance_policy_triggered"}
    governance_trace = [ev for ev in r.trace.events if ev.event_type in governance_events]
    if governance_trace:
        print("\n--- Governance trace events ---")
        for ev in governance_trace:
            print(f"  iter={ev.iteration}  {ev.event_type:<40}  {ev.payload}")

    print("\n--- Planner trace events ---")
    for ev in r.trace.events:
        print(f"  iter={ev.iteration}  {ev.event_type:<45}  {ev.payload}")

    explain_out = r.final_context.task_results.get("explain_value", {})
    if explain_out.get("output"):
        print(f"\n--- Explanation (cognitive) ---\n  {explain_out['output']['text']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    goal = "Store number 10, retrieve it, and explain the retrieved value."

    tool_registry = _build_tool_registry()
    prompt_registry = _build_prompt_registry()
    prompt_capability_registry = _build_prompt_capability_registry()

    exec_llm = _make_execution_llm()
    engine = ExecutionEngine(
        llm_adapter=exec_llm,
        tool_registry=tool_registry,
        prompt_registry=prompt_registry,
    )
    dag_runner = DAGRunner(engine)

    # -------------------------------------------------------------------------
    # Mode A: DETERMINISTIC
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Mode: DETERMINISTIC  (observation-driven)")
    print("=" * 60)

    det_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_deterministic_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
    )
    _print_result(await det_runner.run(goal=goal, session_id="planner-det"))

    # -------------------------------------------------------------------------
    # Mode B: COGNITIVE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Mode: COGNITIVE  (observation-driven)")
    print("=" * 60)

    cog_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_cognitive_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        prompt_capability_registry=prompt_capability_registry,
    )
    _print_result(await cog_runner.run(goal=goal, session_id="planner-cog"))

    # -------------------------------------------------------------------------
    # Scenario C: SUCCESSFUL REPAIR
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario C: SUCCESSFUL REPAIR")
    print("  (planner emits bad tool name → validator rejects → repair fixes)")
    print("=" * 60)

    repair_ok_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_repair_success_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
    )
    _print_result(await repair_ok_runner.run(goal=goal, session_id="planner-repair-ok"))

    # -------------------------------------------------------------------------
    # Scenario D: FAILED REPAIR (safe termination)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario D: FAILED REPAIR  (safe termination)")
    print("  (both initial and repair DAGs are invalid → runner terminates)")
    print("=" * 60)

    repair_fail_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_repair_fail_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
    )
    _print_result(await repair_fail_runner.run(goal="Store a value", session_id="planner-repair-fail"))

    # -------------------------------------------------------------------------
    # Scenario E: RECOVERABLE RUNTIME FAILURE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario E: RECOVERABLE RUNTIME FAILURE")
    print("  (FlakyTool times out → classified TIMEOUT → planner retries → success)")
    print("=" * 60)

    recovery_tool_registry = _build_recovery_tool_registry()
    recovery_engine = ExecutionEngine(
        llm_adapter=exec_llm,
        tool_registry=recovery_tool_registry,
        prompt_registry=prompt_registry,
    )
    recovery_dag_runner = DAGRunner(recovery_engine)
    recovery_memory_e = InMemoryStore()

    recovery_ok_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_recovery_success_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=recovery_dag_runner,
        tool_registry=recovery_tool_registry,
        memory=recovery_memory_e,
        planning_mode=PlanningMode.DETERMINISTIC,
    )
    _print_result(await recovery_ok_runner.run(
        goal="Store number 42 using flaky_store",
        session_id="planner-recovery-ok",
    ))

    # -------------------------------------------------------------------------
    # Scenario F: UNRECOVERABLE RUNTIME FAILURE (safe termination)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario F: UNRECOVERABLE RUNTIME FAILURE  (safe termination)")
    print("  (FatalTool raises unrecoverable error → runner terminates immediately)")
    print("=" * 60)

    recovery_fatal_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_recovery_fatal_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=recovery_dag_runner,
        tool_registry=recovery_tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
    )
    _print_result(await recovery_fatal_runner.run(
        goal="Perform fatal operation",
        session_id="planner-recovery-fatal",
    ))

    # -------------------------------------------------------------------------
    # Scenario G: GOVERNANCE APPROVE (deterministic, safe tools)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario G: GOVERNANCE APPROVE")
    print("  (deterministic, no dangerous tools → all policies APPROVE)")
    print("=" * 60)

    gov_engine = _build_standard_governance()
    gov_approve_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_deterministic_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
        governance_engine=gov_engine,
    )
    _print_result(await gov_approve_runner.run(goal=goal, session_id="planner-gov-approve"))

    # -------------------------------------------------------------------------
    # Scenario H: GOVERNANCE REQUIRE_APPROVAL (cognitive mode)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario H: GOVERNANCE REQUIRE_APPROVAL  (cognitive mode)")
    print("  (CognitiveModeApprovalPolicy fires → execution still proceeds)")
    print("=" * 60)

    gov_cog_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_cognitive_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        prompt_capability_registry=prompt_capability_registry,
        governance_engine=_build_standard_governance(),
    )
    _print_result(await gov_cog_runner.run(goal=goal, session_id="planner-gov-cognitive"))

    # -------------------------------------------------------------------------
    # Scenario I: GOVERNANCE REQUIRE_APPROVAL (dangerous tool)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario I: GOVERNANCE REQUIRE_APPROVAL  (dangerous tool)")
    print("  (DangerousToolPolicy: write_value flagged → REQUIRE_APPROVAL)")
    print("=" * 60)

    gov_dangerous_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_dangerous_tool_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
        governance_engine=_build_dangerous_tool_governance(),
    )
    _print_result(await gov_dangerous_runner.run(
        goal="Write a value and finish",
        session_id="planner-gov-dangerous",
    ))

    # =========================================================================
    # HITL Approval Checkpoint Scenarios (J / K / L)
    # =========================================================================

    # -------------------------------------------------------------------------
    # Scenario J: APPROVAL REQUIRED — cognitive workflow pauses
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario J: APPROVAL REQUIRED (cognitive mode)")
    print("  (CognitiveModeApprovalPolicy → workflow pauses)")
    print("=" * 60)

    approval_store = InMemoryApprovalStore()
    hitl_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_hitl_demo_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        governance_engine=_build_standard_governance(),
        approval_store=approval_store,
    )

    paused_result = await hitl_runner.run(
        goal="Store 42 and confirm it was written.",
        session_id="planner-hitl-cog",
    )
    _print_result(paused_result)

    print(f"\n  Workflow state     : {paused_result.workflow_state.value}")
    print(f"  Approval request   : {paused_result.approval_request_id}")

    pending = approval_store.pending()
    print(f"\n  Pending approvals  : {len(pending)}")
    for req in pending:
        print(f"    id={req.request_id[:8]}...  session={req.session_id}")
        print(f"    reason={req.governance_reason}")
        print(f"    risk_level={req.risk_level}")
        print(f"    triggered_policies={req.triggered_policies}")
        print(f"    proposed_tasks={[t['task_id'] for t in req.proposed_dag.get('tasks', [])]}")

    # -------------------------------------------------------------------------
    # Scenario K: APPROVED RESUME — approve and continue execution
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario K: APPROVED RESUME")
    print("  (approve the request → execution resumes and completes)")
    print("=" * 60)

    if paused_result.approval_request_id:
        approval_store.approve(paused_result.approval_request_id)
        print(f"  Approved request   : {paused_result.approval_request_id[:8]}...")
        resumed_result = await hitl_runner.resume_from_approval(
            paused_result.approval_request_id
        )
        _print_result(resumed_result)
        print(f"\n  Final workflow state: {resumed_result.workflow_state.value}")
    else:
        print("  (no approval request — scenario J did not pause)")

    # -------------------------------------------------------------------------
    # Scenario L: REJECTED WORKFLOW — reject and terminate safely
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario L: REJECTED WORKFLOW  (safe termination)")
    print("  (approval request rejected → workflow terminates immediately)")
    print("=" * 60)

    approval_store_l = InMemoryApprovalStore()
    hitl_runner_l = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_hitl_demo_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        governance_engine=_build_standard_governance(),
        approval_store=approval_store_l,
    )

    paused_l = await hitl_runner_l.run(
        goal="Store 42 and confirm it was written.",
        session_id="planner-hitl-reject",
    )
    print(f"\n  Paused state       : {paused_l.workflow_state.value}")
    print(f"  Approval request   : {paused_l.approval_request_id[:8] if paused_l.approval_request_id else 'N/A'}...")

    if paused_l.approval_request_id:
        approval_store_l.reject(paused_l.approval_request_id)
        print(f"  Rejected request   : {paused_l.approval_request_id[:8]}...")
        rejected_result = await hitl_runner_l.resume_from_approval(
            paused_l.approval_request_id
        )
        _print_result(rejected_result)
        print(f"\n  Final workflow state: {rejected_result.workflow_state.value}")
    else:
        print("  (no approval request)")

    # =========================================================================
    # Durable Persistence Scenarios (M / N / O)
    # =========================================================================

    persist_base = Path(tempfile.mkdtemp()) / "freya_state_mno"
    persistent_store = PersistentWorkflowStore(base_dir=persist_base)
    persist_session_id = "planner-hitl-persist"
    persist_goal = "Store 99 and confirm it was written."

    # -------------------------------------------------------------------------
    # Scenario M: DURABLE PAUSE — snapshot written to disk
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario M: DURABLE PAUSE")
    print("  (workflow pauses + snapshot + approval persisted to disk)")
    print("=" * 60)

    persist_approval_store = InMemoryApprovalStore()
    persist_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_hitl_demo_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        governance_engine=_build_standard_governance(),
        approval_store=persist_approval_store,
        persistent_store=persistent_store,
        runner_id="persist-runner-A",
    )

    paused_m = await persist_runner.run(
        goal=persist_goal,
        session_id=persist_session_id,
    )
    _print_result(paused_m)
    print(f"\n  Workflow state     : {paused_m.workflow_state.value}")
    print(f"  Approval request   : {paused_m.approval_request_id}")

    snapshot_path = persist_base / "workflows" / f"{persist_session_id}.json"
    approval_path = (
        persist_base / "approvals" / f"{paused_m.approval_request_id}.json"
        if paused_m.approval_request_id
        else None
    )
    print(f"\n  Snapshot path      : {snapshot_path}")
    print(f"  Approval path      : {approval_path}")
    print(f"  Snapshot exists    : {snapshot_path.exists()}")
    print(f"  Approval exists    : {approval_path.exists() if approval_path else False}")

    # -------------------------------------------------------------------------
    # Scenario N: SIMULATED RESTART — reconstruct from disk
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario N: SIMULATED RESTART")
    print("  (destroy runner → new runner → restore_workflow() from disk)")
    print("=" * 60)

    # Discard the original runner (simulated process restart).
    del persist_runner

    # In a crash scenario the old runner never released its lease.
    # An admin (or lease TTL) must reclaim it before the new runner can restore.
    # Here we simulate that explicitly.
    orphaned_snap = persistent_store.load_snapshot(persist_session_id)
    if orphaned_snap and orphaned_snap.lease_owner:
        persistent_store.release_lease(persist_session_id, orphaned_snap.lease_owner)
        print(f"\n  Released orphaned lease : {orphaned_snap.lease_owner}")

    # Construct a brand-new runner backed by the same persistent store.
    restored_runner = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_post_restore_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        governance_engine=_build_standard_governance(),
        persistent_store=persistent_store,
    )

    restored_state = restored_runner.restore_workflow(persist_session_id)
    print(f"\n  Restored workflow state   : {restored_state.value}")
    print(f"  Restored session_id       : {persist_session_id}")

    restored_ctx = restored_runner._paused_context  # type: ignore[attr-defined]
    print(f"  Restored goal             : {restored_ctx.goal}")
    print(f"  Restored completed tasks  : {restored_ctx.completed_tasks}")
    print(f"  Restored failed tasks     : {restored_ctx.failed_tasks or '(none)'}")
    print(f"  Restored observation count: {len(restored_ctx.recent_observations)}")
    print("\n  Restored observations:")
    for obs in restored_ctx.recent_observations:
        print(f"    {obs.as_summary()}")

    pending_disk = persistent_store.pending_approvals()
    print(f"\n  Pending approvals on disk  : {len(pending_disk)}")
    for req in pending_disk:
        print(f"    id={req.request_id[:8]}...  reason={req.governance_reason}")

    # -------------------------------------------------------------------------
    # Scenario O: RESUME AFTER RESTART — approve on disk → execute
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario O: RESUME AFTER RESTART")
    print("  (approve on disk → resume_from_approval() on new runner → completes)")
    print("=" * 60)

    if paused_m.approval_request_id:
        persistent_store.approve_approval(paused_m.approval_request_id)
        print(f"  Approved on disk   : {paused_m.approval_request_id[:8]}...")

        resumed_o = await restored_runner.resume_from_approval(
            paused_m.approval_request_id
        )
        _print_result(resumed_o)
        print(f"\n  Final workflow state: {resumed_o.workflow_state.value}")
        print(f"  Completed tasks     : {resumed_o.final_context.completed_tasks}")
    else:
        print("  (no approval request — scenario M did not pause)")

    # =========================================================================
    # Concurrency / Versioning Scenarios (P / Q / R / S)
    # =========================================================================

    concur_base = Path(tempfile.mkdtemp()) / "freya_state_pqrs"
    concur_store = PersistentWorkflowStore(base_dir=concur_base)
    concur_session = "planner-concur"
    concur_goal = "Store 77 and confirm it was written."

    # Shared registries for the concurrency scenarios.
    concur_exec_llm = _make_execution_llm()
    concur_engine = ExecutionEngine(
        llm_adapter=concur_exec_llm,
        tool_registry=tool_registry,
        prompt_registry=prompt_registry,
    )
    concur_dag_runner = DAGRunner(concur_engine)

    # -------------------------------------------------------------------------
    # Scenario P: LEASE ACQUISITION
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario P: LEASE ACQUISITION")
    print("  (runner A pauses workflow; lease acquired; trace emitted)")
    print("=" * 60)

    runner_a = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_hitl_demo_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=concur_dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        governance_engine=_build_standard_governance(),
        persistent_store=concur_store,
        runner_id="runner-A",
    )

    paused_p = await runner_a.run(
        goal=concur_goal,
        session_id=concur_session,
    )
    print(f"\n  Workflow state     : {paused_p.workflow_state.value}")
    print(f"  Approval request   : {paused_p.approval_request_id}")

    snap_p = concur_store.load_snapshot(concur_session)
    print(f"\n  Snapshot version   : {snap_p.version}")
    print(f"  Lease owner        : {snap_p.lease_owner}")
    print(f"  Lease expires      : {snap_p.lease_expires_at}")

    lease_events = [
        ev for ev in paused_p.trace.events
        if ev.event_type in {"workflow_lease_acquired", "workflow_snapshot_persisted"}
    ]
    print("\n  Lease/snapshot trace events:")
    for ev in lease_events:
        print(f"    {ev.event_type:<40}  {ev.payload}")

    # -------------------------------------------------------------------------
    # Scenario Q: CONCURRENT RESUME REJECTED
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario Q: CONCURRENT RESUME REJECTED")
    print("  (runner B tries restore_workflow while runner A holds lease)")
    print("=" * 60)

    runner_b = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_post_restore_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=concur_dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        governance_engine=_build_standard_governance(),
        persistent_store=concur_store,
        runner_id="runner-B",
    )

    try:
        runner_b.restore_workflow(concur_session)
        print("  ERROR: expected WorkflowLeaseError but got none")
    except WorkflowLeaseError as exc:
        print(f"  WorkflowLeaseError (expected): {exc}")

    # -------------------------------------------------------------------------
    # Scenario R: STALE SNAPSHOT WRITE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario R: STALE SNAPSHOT WRITE")
    print("  (attempt to save with wrong expected_version → conflict error)")
    print("=" * 60)

    current_snap = concur_store.load_snapshot(concur_session)
    stale_snap = current_snap.model_copy(update={"goal": "stale attempt"})

    try:
        concur_store.save_snapshot(stale_snap, expected_version=0)
        print("  ERROR: expected WorkflowVersionConflictError but got none")
    except WorkflowVersionConflictError as exc:
        print(f"  WorkflowVersionConflictError (expected):")
        print(f"    session_id       : {exc.session_id}")
        print(f"    expected_version : {exc.expected_version}")
        print(f"    actual_version   : {exc.actual_version}")

    # -------------------------------------------------------------------------
    # Scenario S: SUCCESSFUL RESUME AFTER LEASE TRANSFER
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario S: SUCCESSFUL RESUME AFTER LEASE TRANSFER")
    print("  (runner A releases lease → runner B restores + resumes)")
    print("=" * 60)

    # Runner A releases its lease.
    concur_store.release_lease(concur_session, "runner-A")
    snap_after_release = concur_store.load_snapshot(concur_session)
    print(f"\n  Lease after release : {snap_after_release.lease_owner!r}")

    # Runner B now restores successfully.
    restored_state_s = runner_b.restore_workflow(concur_session)
    print(f"  Runner B restored   : {restored_state_s.value}")

    snap_b = concur_store.load_snapshot(concur_session)
    print(f"  Lease owner (B)     : {snap_b.lease_owner}")
    print(f"  Snapshot version    : {snap_b.version}")

    # Approve the request and resume via runner B.
    if paused_p.approval_request_id:
        concur_store.approve_approval(paused_p.approval_request_id)
        print(f"  Approved on disk    : {paused_p.approval_request_id[:8]}...")

        resumed_s = await runner_b.resume_from_approval(paused_p.approval_request_id)
        _print_result(resumed_s)
        print(f"\n  Final workflow state: {resumed_s.workflow_state.value}")
        print(f"  Completed tasks     : {resumed_s.final_context.completed_tasks}")

        lease_rel_events = [
            ev for ev in resumed_s.trace.events
            if ev.event_type in {
                "workflow_lease_acquired",
                "workflow_lease_released",
                "workflow_snapshot_restored",
            }
        ]
        print("\n  Lease/restore trace events:")
        for ev in lease_rel_events:
            print(f"    {ev.event_type:<40}  {ev.payload}")
    else:
        print("  (no approval request — scenario P did not pause)")

    # =========================================================================
    # Event Bus Scenarios (T / U / V)
    # =========================================================================

    # -------------------------------------------------------------------------
    # Scenario T: EVENT STREAM
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario T: EVENT STREAM")
    print("  (InProcessEventBus; TraceSubscriber + GovernanceAuditSubscriber)")
    print("=" * 60)

    event_bus_t = InProcessEventBus()
    trace_sub = TraceSubscriber()
    gov_audit_sub = GovernanceAuditSubscriber()
    event_bus_t.subscribe(trace_sub)
    event_bus_t.subscribe(gov_audit_sub)

    det_runner_t = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_deterministic_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
        event_bus=event_bus_t,
    )
    result_t = await det_runner_t.run(goal=goal, session_id="planner-event-t")
    _print_result(result_t)

    print("\n  --- Ordered runtime event stream ---")
    for ev in event_bus_t.recent_events():
        print(f"  {ev.event_type:<45}  iter={ev.iteration}  state={ev.workflow_state or '-'}")

    print(f"\n  Replay buffer size    : {len(event_bus_t.recent_events(limit=200))}")
    print(f"  Governance audit log  : {len(gov_audit_sub.audit_log)} entries")
    print(f"  Trace subscriber entries: {len(trace_sub.entries)}")

    # -------------------------------------------------------------------------
    # Scenario U: SUBSCRIBER FAILURE ISOLATION
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario U: SUBSCRIBER FAILURE ISOLATION")
    print("  (crashing subscriber; workflow still completes; failure event emitted)")
    print("=" * 60)

    class _CrashingSubscriber:
        """Always raises to verify bus isolation."""
        async def handle_event(self, event: RuntimeEvent) -> None:
            raise RuntimeError(f"intentional crash on {event.event_type!r}")

    event_bus_u = InProcessEventBus()
    trace_sub_u = TraceSubscriber()
    event_bus_u.subscribe(_CrashingSubscriber())
    event_bus_u.subscribe(trace_sub_u)

    det_runner_u = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_deterministic_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
        event_bus=event_bus_u,
    )
    result_u = await det_runner_u.run(goal=goal, session_id="planner-event-u")
    _print_result(result_u)

    failure_events = [
        ev for ev in event_bus_u.recent_events()
        if ev.event_type == EventType.SUBSCRIBER_FAILURE
    ]
    print(f"\n  subscriber_failure events : {len(failure_events)}")
    for ev in failure_events[:3]:
        print(f"    subscriber={ev.payload.get('subscriber_name')!r}  "
              f"failed_on={ev.payload.get('failed_event_type')!r}  "
              f"error={ev.payload.get('error')!r}")
    print(f"  Workflow still completed  : {result_u.workflow_state.value}")
    print(f"  TraceSubscriber received  : {len(trace_sub_u.entries)} events (isolation works)")

    # -------------------------------------------------------------------------
    # Scenario V: PERSISTENCE SUBSCRIBER
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario V: PERSISTENCE SUBSCRIBER")
    print("  (workflow pauses; PersistenceSubscriber auto-persists via event bus)")
    print("=" * 60)

    persist_base_v = Path(tempfile.mkdtemp()) / "freya_state_v"
    persistent_store_v = PersistentWorkflowStore(base_dir=persist_base_v)

    event_bus_v = InProcessEventBus()
    trace_sub_v = TraceSubscriber()
    gov_audit_v = GovernanceAuditSubscriber()
    event_bus_v.subscribe(trace_sub_v)
    event_bus_v.subscribe(gov_audit_v)

    # InMemoryApprovalStore for the in-process pause lookup (no persistent store needed
    # for the bus integration test — PersistenceSubscriber is wired separately).
    approval_store_v = InMemoryApprovalStore()

    hitl_runner_v = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_hitl_demo_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        governance_engine=_build_standard_governance(),
        approval_store=approval_store_v,
        persistent_store=persistent_store_v,
        event_bus=event_bus_v,
    )

    paused_v = await hitl_runner_v.run(
        goal="Store 55 and confirm.",
        session_id="planner-event-v",
    )
    print(f"\n  Workflow state       : {paused_v.workflow_state.value}")
    print(f"  Approval request     : {paused_v.approval_request_id}")

    snap_path_v = persist_base_v / "workflows" / "planner-event-v.json"
    print(f"\n  Snapshot on disk     : {snap_path_v.exists()}")
    print(f"  Snapshot path        : {snap_path_v}")

    persist_events_v = [
        ev for ev in event_bus_v.recent_events()
        if ev.event_type in {
            EventType.WORKFLOW_PAUSED_FOR_APPROVAL,
            EventType.WORKFLOW_SNAPSHOT_PERSISTED,
            EventType.WORKFLOW_LEASE_ACQUIRED,
        }
    ]
    print(f"\n  Persistence-related events in bus ({len(persist_events_v)}):")
    for ev in persist_events_v:
        print(f"    {ev.event_type:<45}  payload={ev.payload}")

    print(f"\n  Governance audit entries : {len(gov_audit_v.audit_log)}")
    for entry in gov_audit_v.audit_log:
        print(f"    {entry['event_type']:<45}  session={entry['session_id']}")

    # =========================================================================
    # Multi-Workflow Coordination Scenarios (W / X / Y / Z)
    # =========================================================================

    recovery_tool_registry = _build_recovery_tool_registry()

    # -------------------------------------------------------------------------
    # Scenario W: SUBWORKFLOW DELEGATION
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario W: SUBWORKFLOW DELEGATION")
    print("  (parent spawns child subworkflow; child completes; parent continues)")
    print("=" * 60)

    coordinator_w = WorkflowCoordinator()

    runner_w = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_subworkflow_w_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
        coordinator=coordinator_w,
    )

    result_w = await runner_w.run(
        goal="Analyze logs and verify results.",
        session_id="w-parent",
    )

    print(f"\n  Parent workflow state: {result_w.workflow_state.value}")
    print(f"  Completed tasks     : {result_w.final_context.completed_tasks}")
    print(f"  Child summaries     : {result_w.final_context.child_workflow_summaries}")

    coord_events_w = [
        ev for ev in result_w.trace.events
        if ev.event_type in {"subworkflow_spawned", "subworkflow_completed",
                              "subworkflow_failed", "workflow_relationship_created"}
    ]
    print(f"\n  Coordination trace events ({len(coord_events_w)}):")
    for ev in coord_events_w:
        print(f"    iter={ev.iteration}  {ev.event_type}")

    children_w = coordinator_w.get_children("w-parent")
    print(f"\n  Children of w-parent : {children_w}")
    print(f"  Observation summaries:")
    for obs in result_w.final_context.recent_observations:
        print(f"    [{obs.status}] {obs.task_id}: {obs.semantic_summary or obs.as_summary()}")

    # -------------------------------------------------------------------------
    # Scenario X: CHILD FAILURE OBSERVATION
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario X: CHILD FAILURE OBSERVATION")
    print("  (child workflow fails; parent observes summarized failure; parent adapts)")
    print("=" * 60)

    coordinator_x = WorkflowCoordinator()

    runner_x = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_subworkflow_x_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=recovery_dag_runner,
        tool_registry=recovery_tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.DETERMINISTIC,
        coordinator=coordinator_x,
    )

    result_x = await runner_x.run(
        goal="Classify the security incident.",
        session_id="x-parent",
    )

    print(f"\n  Parent workflow state: {result_x.workflow_state.value}")
    print(f"  Child summaries     : {result_x.final_context.child_workflow_summaries}")

    failed_children_x = [s for s in result_x.final_context.child_workflow_summaries if "failed" in s]
    print(f"\n  Failed child summaries ({len(failed_children_x)}):")
    for s in failed_children_x:
        print(f"    {s}")

    coord_events_x = [
        ev for ev in result_x.trace.events
        if ev.event_type in {"subworkflow_spawned", "subworkflow_failed"}
    ]
    print(f"\n  Coordination events:")
    for ev in coord_events_x:
        print(f"    {ev.event_type:<35}  payload={ev.payload}")

    print(f"\n  Parent observations (summarized, no raw child traces):")
    for obs in result_x.final_context.recent_observations:
        print(f"    [{obs.task_type or 'tool'}] {obs.status}: {obs.semantic_summary or obs.as_summary()}")

    # -------------------------------------------------------------------------
    # Scenario Y: WORKFLOW TREE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario Y: WORKFLOW TREE")
    print("  (render hierarchical workflow tree)")
    print("=" * 60)

    coordinator_y = WorkflowCoordinator()
    coordinator_y.spawn_subworkflow("planner-root", "planner-root-child-1")
    coordinator_y.spawn_subworkflow("planner-root-child-1", "planner-root-child-1-recovery",
                                    relationship_type=RelationshipType.RECOVERY_SUBWORKFLOW)
    coordinator_y.spawn_subworkflow("planner-root", "planner-root-child-2",
                                    relationship_type=RelationshipType.DELEGATED_EXECUTION)

    tree_str_y = render_workflow_tree(coordinator_y, "planner-root")
    print("\n  Workflow tree:")
    for line in tree_str_y.splitlines():
        print(f"    {line}")

    # Also show coordinator_w tree from Scenario W
    print(f"\n  Coordinator W tree (root=w-parent):")
    if coordinator_w.get_children("w-parent"):
        for line in render_workflow_tree(coordinator_w, "w-parent").splitlines():
            print(f"    {line}")
    else:
        print("    w-parent (no children registered)")

    print(f"\n  All relationships in coordinator_y:")
    for rel in coordinator_y.all_relationships():
        print(f"    {rel.parent_session_id} → {rel.child_session_id}  [{rel.relationship_type}]")

    # -------------------------------------------------------------------------
    # Scenario Z: GOVERNANCE INHERITED
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Scenario Z: GOVERNANCE INHERITED")
    print("  (child workflow pauses for approval independently; governance shared)")
    print("=" * 60)

    coordinator_z = WorkflowCoordinator()
    event_bus_z = InProcessEventBus()
    trace_sub_z = TraceSubscriber()
    event_bus_z.subscribe(trace_sub_z)

    governance_z = _build_standard_governance()  # CognitiveModeApprovalPolicy included
    approval_store_z = InMemoryApprovalStore()

    # Register the parent-child relationship in coordinator
    z_parent_session = "z-parent"
    z_child_session = "z-child"
    coordinator_z.spawn_subworkflow(z_parent_session, z_child_session)

    # Child runner inherits: governance, event_bus, coordinator (independent state/leases/snapshots)
    child_runner_z = IterativePlannerRunner(
        planner=SimpleIterativePlanner(
            llm_adapter=_make_hitl_demo_planner_llm(),
            prompt_registry=prompt_registry,
        ),
        dag_runner=dag_runner,
        tool_registry=tool_registry,
        memory=InMemoryStore(),
        planning_mode=PlanningMode.COGNITIVE,
        prompt_capability_registry=prompt_capability_registry,
        governance_engine=governance_z,
        approval_store=approval_store_z,
        event_bus=event_bus_z,
        coordinator=coordinator_z,
    )

    # Child runs independently — inherits governance → CognitiveModeApprovalPolicy fires
    paused_z = await child_runner_z.run(
        goal="Audit and store security configuration.",
        session_id=z_child_session,
    )

    print(f"\n  Child workflow state: {paused_z.workflow_state.value}")
    print(f"  Child approval req : {paused_z.approval_request_id}")
    print(f"  Child is independent (own state, own lease, own snapshot)")

    # Approve the child's governance checkpoint (parent coordinates)
    if (
        paused_z.workflow_state == WorkflowState.PAUSED_FOR_APPROVAL
        and paused_z.approval_request_id
    ):
        approval_store_z.approve(paused_z.approval_request_id)
        resumed_z = await child_runner_z.resume_from_approval(paused_z.approval_request_id)
        print(f"\n  Child resumed and completed: {resumed_z.workflow_state.value}")
        print(f"  Child completed tasks      : {resumed_z.final_context.completed_tasks}")
    else:
        print("  (child did not pause — unexpected)")

    gov_events_z = [
        ev for ev in trace_sub_z.entries
        if "governance" in ev["event_type"] or "approval" in ev["event_type"]
    ]
    print(f"\n  Governance/approval events in shared bus ({len(gov_events_z)}):")
    for ev in gov_events_z:
        print(f"    {ev['event_type']:<50}  session={ev['session_id']}")

    print(f"\n  Workflow tree (z-parent → z-child):")
    for line in render_workflow_tree(coordinator_z, z_parent_session).splitlines():
        print(f"    {line}")

    print()


if __name__ == "__main__":
    asyncio.run(main())
