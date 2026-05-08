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
* Durable workflow persistence
* WorkflowSnapshot
* PersistentWorkflowStore
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

# Workflow Versioning + Concurrency Safety

IMPORTANT:
This step introduces:

* optimistic concurrency control
* workflow versioning
* resume safety
* execution leases
* stale snapshot protection

This step does NOT introduce:

* distributed databases
* Redis
* Kafka
* Kubernetes
* networked coordination
* leader election

Keep implementation:

* local
* deterministic
* file-based
* inspectable

DO NOT rewrite runtime architecture.

---

# ARCHITECTURE GOAL

Freya currently supports:

* durable workflow snapshots
* restart-safe approval recovery
* resumable cognition execution

BUT:
multiple runners can still:

* restore same workflow
* resume same approval
* overwrite snapshots concurrently

This can corrupt workflow state.

Now Freya must support:

* snapshot versioning
* optimistic locking
* workflow leases
* stale resume protection

WITHOUT:

* introducing distributed systems
* mutating completed tasks
* breaking deterministic execution

---

# REQUIREMENTS

## 1. Add Snapshot Versioning

Update:

WorkflowSnapshot

Add:

* version: int
* lease_owner: str | None
* lease_expires_at: datetime | None

Rules:

* every successful snapshot write increments version
* restores preserve current version
* stale writes must fail

---

## 2. Add Concurrency Errors

Create:

freya/governance/errors.py

Define:

* WorkflowVersionConflictError
* WorkflowLeaseError
* WorkflowAlreadyResumedError

Use explicit typed exceptions.

---

## 3. Add Atomic Snapshot Save

Update:

PersistentWorkflowStore.save_snapshot()

Behavior:

* compare expected_version
* reject stale writes
* increment version atomically

Method signature:

save_snapshot(
snapshot,
expected_version: int | None = None,
)

Rules:

* if current persisted version != expected_version
  → raise WorkflowVersionConflictError

Use atomic temp-file replace semantics.

---

## 4. Add Workflow Lease Support

Add methods:

acquire_lease(
session_id,
owner_id,
ttl_seconds=30,
)

release_lease(
session_id,
owner_id,
)

Rules:

* only one runner may hold lease
* expired leases may be reclaimed
* lease owner required for resume operations

Leases stored inside snapshot.

---

## 5. Add Resume Protection

Update:

resume_from_approval()

Behavior:

* require valid workflow lease
* reject duplicate resume attempts
* reject stale approvals
* reject already-completed workflows

Raise:

* WorkflowLeaseError
* WorkflowAlreadyResumedError

---

## 6. Add Runner Identity

Update:

IterativePlannerRunner

Add:

runner_id: str

Default:
uuid4()

All persistence + lease operations use runner_id.

---

## 7. Add Snapshot State Validation

On restore:

validate:

* workflow_state consistency
* approval linkage
* snapshot version validity

Reject corrupted snapshots safely.

---

## 8. Add Concurrency Trace Events

Add:

workflow_lease_acquired
workflow_lease_released
workflow_version_conflict
workflow_resume_rejected

Example payloads:

{
"session_id": "...",
"runner_id": "...",
"version": 4
}

---

## 9. Example Scenarios

Update examples/run_planner.py

Demonstrate:

### Scenario P — Lease Acquisition

* runner A acquires workflow lease
* lease trace emitted

### Scenario Q — Concurrent Resume Rejected

* runner B attempts resume
* rejected due to active lease

### Scenario R — Stale Snapshot Write

* outdated snapshot save attempted
* WorkflowVersionConflictError raised

### Scenario S — Successful Resume After Lease Transfer

* lease released
* second runner resumes successfully

Print:

* versions
* lease owners
* lease expiration
* concurrency failures

---

## 10. HARD RULES

DO NOT:

* add Redis
* add distributed locks
* add networking
* add threads/process pools
* rerun completed tasks
* silently overwrite snapshots
* allow multiple concurrent resumes

Concurrency safety must remain:

* deterministic
* local
* inspectable
* optimistic-lock based

---

## 11. DESIGN INTENT

This step transitions Freya from:

* durable cognition runtime

to:

* concurrency-safe governed cognition runtime

Workflows become:

* versioned
* lease-protected
* resume-safe
* corruption-resistant

WITHOUT introducing distributed orchestration.

This is foundational runtime correctness infrastructure.

---

# OUTPUT FORMAT

Provide:

1. Snapshot versioning updates
2. Concurrency exceptions
3. Lease implementation
4. Optimistic locking
5. Resume protection
6. Trace integration
7. Updated examples

Do NOT explain.
Only output code.
