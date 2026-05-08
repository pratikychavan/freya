You are working inside the Freya SDK repository.

Freya already supports:

* ExecutionEngine
* DAGRunner
* IterativePlannerRunner
* PlanningContext
* Observation-aware planning
* Validation + Repair loop
* Runtime failure recovery
* GovernanceEngine
* Approval checkpoints
* InMemoryApprovalStore
* WorkflowState
* ToolRegistry
* PromptRegistry
* PromptCapabilityRegistry
* PlanningMode
* Memory layer
* Trace system
* Deterministic and Cognitive planner modes

The architecture is stable and modular.

Your task is to implement:

# Persistent Workflow State (Durable HITL Runtime)

IMPORTANT:
This step introduces:

* durable workflow persistence
* resumable workflow snapshots
* crash-safe approval recovery
* workflow state serialization

This step does NOT introduce:

* distributed execution
* databases
* web APIs
* RBAC
* event buses
* Kubernetes orchestration

Persistence should remain:

* local
* file-based
* deterministic
* inspectable

DO NOT rewrite runtime architecture.

---

# ARCHITECTURE GOAL

Freya currently supports:

* pause/resume workflows
* approval checkpoints
* in-memory approval state

BUT:
all workflow state is lost on process restart.

Now Freya must support:

* persistent workflow snapshots
* persistent approval requests
* crash recovery
* durable resume semantics

WITHOUT:

* rerunning completed tasks
* losing observations
* rebuilding planner context from scratch
* restarting workflows

---

# REQUIREMENTS

## 1. Add WorkflowSnapshot Model

Create:

freya/governance/snapshot.py

Define:

WorkflowSnapshot:

* snapshot_id: str
* session_id: str
* workflow_state: WorkflowState
* iteration: int
* planning_mode: str
* goal: str
* completed_tasks: list[str]
* failed_tasks: list[str]
* task_results: dict
* recent_observations: list[dict]
* memory_state: dict
* paused_dag_fragment: dict | None
* approval_request_id: str | None
* created_at: datetime
* updated_at: datetime

Use Pydantic v2.

Generate snapshot_id with uuid4().

---

## 2. Add PersistentWorkflowStore

Create:

freya/governance/persistent_store.py

Responsibilities:

* persist workflow snapshots to disk
* load workflow snapshots
* persist approval requests
* restore workflow state after restart

Storage format:

* JSON files only

Suggested structure:

.freya_state/
workflows/
<session_id>.json
approvals/
<request_id>.json

Methods:

* save_snapshot(snapshot)

* load_snapshot(session_id)

* delete_snapshot(session_id)

* save_approval(request)

* load_approval(request_id)

* pending_approvals()

Implementation MUST:

* be deterministic
* use atomic writes
* remain inspectable by humans

DO NOT use databases.

---

## 3. Add Snapshot Serialization

Update:

* PlanningContext
* ApprovalRequest
* Observation

Add:

* to_dict()
* from_dict()

All workflow state must be serializable.

DO NOT serialize:

* live engine objects
* planner instances
* runtime locks
* async handles

Only serialize execution state.

---

## 4. Persist State on Pause

Update IterativePlannerRunner.

When workflow pauses:

* create WorkflowSnapshot
* persist snapshot
* persist ApprovalRequest

Workflow MUST be resumable after process restart.

---

## 5. Add Restore + Resume

Add method:

restore_workflow(
session_id: str
)

Behavior:

* load WorkflowSnapshot
* reconstruct PlanningContext
* restore observations
* restore memory state
* restore workflow state

Then:

resume_from_approval(request_id)

must work even after:

* process restart
* runner reconstruction

---

## 6. Add Memory Persistence

Persist:

* session KV state

When restored:

* memory must contain prior values
* completed tasks must remain completed

DO NOT rerun prior successful tasks.

---

## 7. Add Crash Recovery Scenario

Update examples/run_planner.py

Demonstrate:

### Scenario M — Durable Pause

* workflow pauses for approval
* snapshot written to disk

### Scenario N — Simulated Restart

* destroy runner instance
* construct NEW runner
* restore workflow from disk

### Scenario O — Resume After Restart

* approve request
* resume workflow
* execution continues correctly

Print:

* snapshot paths
* restored workflow state
* restored observations
* restored completed tasks

---

## 8. Add Persistence Trace Events

Add:

workflow_snapshot_persisted
workflow_snapshot_restored
workflow_state_restored

Example payloads:

{
"session_id": "planner-hitl-cog",
"snapshot_path": "..."
}

---

## 9. HARD RULES

DO NOT:

* rerun completed tasks
* serialize runtime internals
* serialize planner objects
* rebuild workflow from scratch
* add databases
* add distributed systems
* add networking

Persistence must remain:

* local
* deterministic
* resumable
* inspectable

---

## 10. DESIGN INTENT

This step transitions Freya from:

* process-local governed cognition

to:

* durable governed cognition runtime

Planner:

* remains stateless

Workflow state:

* becomes durable

Governance:

* becomes restart-safe

Execution:

* becomes resumable across process restarts

This is NOT distributed orchestration yet.

This is durable local cognition lifecycle management.

---

# OUTPUT FORMAT

Provide:

1. WorkflowSnapshot model
2. PersistentWorkflowStore
3. Serialization helpers
4. Pause persistence integration
5. Restore/resume implementation
6. Updated examples
7. Trace integration

Do NOT explain.
Only output code.
