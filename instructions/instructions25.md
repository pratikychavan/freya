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
* Workflow versioning
* Workflow leases
* Optimistic concurrency control
* Resume-safe execution
* Internal event-driven runtime architecture
* RuntimeEvent
* InProcessEventBus
* Event subscribers
* Trace system
* Deterministic and Cognitive planner modes

The architecture is stable and modular.

Your task is to implement:

# Multi-Workflow Coordination (Hierarchical Governed Execution)

IMPORTANT:
This step introduces:

* parent workflows
* child workflows
* workflow delegation
* subworkflow execution
* workflow dependency tracking
* governed workflow coordination

This step does NOT introduce:

* autonomous agent swarms
* peer-to-peer agents
* distributed execution
* networking
* microservices
* message brokers

Keep implementation:

* local
* deterministic
* inspectable
* hierarchy-driven

DO NOT rewrite runtime architecture.

---

# ARCHITECTURE GOAL

Freya currently supports:

* single governed workflows
* pause/resume execution
* persistence
* concurrency safety
* event-driven orchestration

BUT:
all workflows are isolated.

Now Freya must support:

* workflows spawning subworkflows
* parent-child execution relationships
* delegated execution
* workflow dependency management
* governed subworkflow coordination

WITHOUT:

* uncontrolled agent communication
* distributed orchestration
* recursive chaos

This is NOT "multi-agent AI".

This is:

* hierarchical governed workflow execution.

---

# REQUIREMENTS

## 1. Add WorkflowRelationship Models

Create:

freya/workflows/models.py

Define:

WorkflowRelationship:

* parent_session_id: str
* child_session_id: str
* relationship_type: str
* created_at: datetime

Relationship types:

* spawned_subworkflow
* delegated_execution
* recovery_subworkflow

Use Pydantic v2.

---

## 2. Add WorkflowCoordinator

Create:

freya/workflows/coordinator.py

Responsibilities:

* spawn child workflows
* track workflow relationships
* coordinate workflow completion
* aggregate child workflow status

Methods:

* spawn_subworkflow(...)
* get_children(session_id)
* get_parent(session_id)
* workflow_tree(session_id)

Coordinator must remain:

* deterministic
* local
* inspectable

---

## 3. Add Subworkflow Execution

Update IterativePlannerRunner.

Allow DAG tasks:

{
"task_id": "analyze_logs",
"type": "subworkflow",
"input": {
"goal": "...",
"planning_mode": "cognitive"
}
}

Behavior:

* spawn child workflow
* execute child runner
* wait for completion
* capture child result
* inject child observations into parent

Subworkflow execution MUST:

* preserve governance
* preserve persistence
* preserve event semantics

---

## 4. Add Workflow Dependency Tracking

Parent workflow must track:

* child workflow IDs
* child completion status
* child failures
* child observations

Add to PlanningContext:

* child_workflow_summaries

---

## 5. Add Child Workflow Observations

Parent observations should include summaries like:

"subworkflow analyze_logs completed successfully"
"subworkflow classify_incident failed due to timeout"

DO NOT inject raw child traces.

Only summarized observations.

---

## 6. Add Governance Inheritance

Child workflows inherit:

* governance policies
* event bus
* persistence store
* runtime configuration

BUT:
child workflows get:

* independent workflow state
* independent leases
* independent snapshots

---

## 7. Add Workflow Coordination Events

Add events:

subworkflow_spawned
subworkflow_completed
subworkflow_failed
workflow_relationship_created

Payload examples:

{
"parent_session_id": "...",
"child_session_id": "...",
"relationship_type": "spawned_subworkflow"
}

---

## 8. Add Workflow Tree Visualization Helper

Add helper:

render_workflow_tree(session_id)

Output example:

planner-root
├── planner-root-child-1
│   └── planner-root-child-1-recovery
└── planner-root-child-2

Text-only tree rendering is sufficient.

---

## 9. Add Failure Propagation Rules

Rules:

* child failure does NOT automatically crash parent
* parent planner decides next step based on observations
* governance still applies independently

This preserves:

* adaptive coordination
* governed delegation

---

## 10. Example Scenarios

Update examples/run_planner.py

Demonstrate:

### Scenario W — Subworkflow Delegation

* parent workflow spawns child
* child completes successfully
* parent continues

### Scenario X — Child Failure Observation

* child workflow fails
* parent observes summarized failure
* parent adapts

### Scenario Y — Workflow Tree

* render workflow hierarchy

### Scenario Z — Governance Inherited

* child workflow pauses for approval independently

Print:

* workflow trees
* child summaries
* coordination events
* parent observations

---

## 11. HARD RULES

DO NOT:

* create peer-to-peer agents
* allow unrestricted workflow communication
* add networking
* add distributed execution
* add message brokers
* allow children to mutate parent runtime directly

Hierarchy must remain:

* explicit
* governed
* deterministic
* inspectable

---

## 12. DESIGN INTENT

This step transitions Freya from:

* single governed workflows

to:

* hierarchical governed adaptive execution

Parent workflows:

* coordinate delegation

Child workflows:

* execute independently

Governance:

* remains enforceable at every level

This is NOT autonomous agent swarms.

This is:

* governed hierarchical cognition orchestration.

---

# OUTPUT FORMAT

Provide:

1. Workflow relationship models
2. WorkflowCoordinator
3. Subworkflow execution support
4. Coordination events
5. Workflow tree rendering
6. Parent-child observation integration
7. Updated examples

Do NOT explain.
Only output code.
