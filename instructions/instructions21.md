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
* InterventionPolicy
* GovernanceDecision
* ToolRegistry
* PromptRegistry
* PromptCapabilityRegistry
* PlanningMode
* Memory layer
* Trace system
* Deterministic and Cognitive planner modes

The architecture is stable and modular.

Your task is to implement:

# STEP 2 — Approval Checkpoints (Workflow Pausing)

IMPORTANT:
This step introduces:

* workflow pausing
* approval checkpoints
* approval artifacts
* resumable execution state

This step does NOT introduce:

* databases
* web APIs
* UI
* Slack/email integrations
* RBAC/auth systems

Keep implementation:

* in-memory
* deterministic
* resumable
* observable

DO NOT rewrite runtime architecture.

---

# ARCHITECTURE GOAL

Freya governance currently:

* evaluates DAG fragments
* emits REQUIRE_APPROVAL decisions

BUT execution still continues.

Now Freya must support:

governance → REQUIRE_APPROVAL
→ execution PAUSES before DAG execution
→ approval request created
→ workflow becomes resumable

This introduces:

* governed execution checkpoints
* human-controlled delegation boundaries

WITHOUT:

* planner-user coupling
* runtime instability
* loss of deterministic execution

---

# REQUIREMENTS

## 1. Add WorkflowState Enum

Create:

freya/governance/state.py

Define:

class WorkflowState(str, Enum):
RUNNING = "running"
PAUSED_FOR_APPROVAL = "paused_for_approval"
APPROVED = "approved"
REJECTED = "rejected"
COMPLETED = "completed"
FAILED = "failed"

---

## 2. Add ApprovalRequest Model

Create:

freya/governance/approval.py

Define:

ApprovalRequest:

* request_id: str
* session_id: str
* iteration: int
* proposed_dag: dict
* governance_reason: str
* risk_level: str | None
* triggered_policies: list[str]
* observation_summaries: list[str]
* created_at: datetime
* state: WorkflowState

Use Pydantic v2.

Generate request_id with uuid4().

---

## 3. Add InMemoryApprovalStore

Create:

freya/governance/store.py

Responsibilities:

* store ApprovalRequest
* retrieve request
* approve request
* reject request
* list pending requests

Methods:

* create(request)
* get(request_id)
* approve(request_id)
* reject(request_id)
* pending()

Store everything in-memory only.

---

## 4. Add Pause Semantics to IterativePlannerRunner

Update runner behavior:

Current:
planner
→ governance
→ execution continues

New:
planner
→ governance
→ REQUIRE_APPROVAL?
YES:
- create ApprovalRequest
- emit pause traces
- stop execution safely
- return paused result
NO:
- continue execution

Execution MUST NOT occur after pause.

---

## 5. Add PlannerResult Workflow State

Extend PlannerResult:

workflow_state: WorkflowState
approval_request_id: str | None

---

## 6. Add Resume API

Add method:

resume_from_approval(
request_id: str
)

Behavior:

If approved:

* continue execution from paused DAG fragment

If rejected:

* terminate safely

DO NOT:

* restart workflow from beginning
* regenerate planner state
* lose observations
* rerun completed tasks

Resume must continue from checkpoint.

---

## 7. Add Governance Trace Events

Add:

workflow_paused_for_approval
workflow_resumed_after_approval
workflow_rejected_by_governance

Example payloads:

{
"request_id": "...",
"risk_level": "high"
}

---

## 8. Add Approval Observations

When paused:

Add observation summary:

"workflow paused awaiting approval due to governance policy"

When resumed:

"workflow resumed after approval"

When rejected:

"workflow rejected by governance"

---

## 9. Update Governance Behavior

Policies still remain:

* deterministic
* advisory

BUT:
runner now ENFORCES governance decisions.

Governance layer itself must NOT:

* pause runtime directly
* mutate execution
* call resume logic

Keep governance and execution separate.

---

## 10. Example Scenarios

Update examples/run_planner.py

Demonstrate:

### Scenario A — APPROVAL REQUIRED

* cognitive workflow
* governance triggers REQUIRE_APPROVAL
* workflow pauses
* approval request printed

### Scenario B — APPROVED RESUME

* approve request in-memory
* resume workflow
* execution continues successfully

### Scenario C — REJECTED WORKFLOW

* reject request
* workflow terminates safely

Print:

* workflow state
* approval request IDs
* pending approvals
* resume behavior

---

## 11. HARD RULES

DO NOT:

* add databases
* add APIs
* add UI
* add async queues
* rerun completed tasks
* lose execution state during pause
* regenerate planner context after approval

Pause/resume must remain:

* local
* deterministic
* resumable
* observable

---

## 12. DESIGN INTENT

This step introduces:

Human-Governed Execution Checkpoints

Planner:

* proposes

Governance:

* evaluates risk

Runtime:

* pauses execution safely

Human:

* controls delegation boundary

This is NOT autonomous approval reasoning.

This is governed execution infrastructure.

---

# OUTPUT FORMAT

Provide:

1. Workflow state models
2. ApprovalRequest implementation
3. InMemoryApprovalStore
4. Runner pause/resume integration
5. Trace integration
6. Updated examples

Do NOT explain.
Only output code.
