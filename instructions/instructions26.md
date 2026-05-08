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
* Multi-workflow coordination
* WorkflowCoordinator
* Hierarchical governed execution
* Subworkflow execution
* Workflow trees
* Trace system
* Deterministic and Cognitive planner modes

The architecture is stable and modular.

Your task is to implement:

# Capability-Aware Delegation + Planning Contracts

IMPORTANT:
This step introduces:

* explicit delegation contracts
* capability-aware subworkflow spawning
* delegation reasoning
* execution expectations
* governance-aware delegation constraints

This step does NOT introduce:

* autonomous swarms
* peer-to-peer agents
* distributed orchestration
* networking
* ML training
* vector databases

Keep implementation:

* deterministic
* explicit
* inspectable
* contract-driven

DO NOT rewrite runtime architecture.

---

# ARCHITECTURE GOAL

Freya currently supports:

* parent workflows
* child workflows
* delegated execution
* hierarchical coordination

BUT:
delegation semantics are implicit.

Currently:

* planner decides to spawn child
* runtime executes child
* no formal delegation contract exists

Now Freya must support:

* explicit delegation contracts
* required capabilities
* expected outputs
* delegation rationale
* execution budgets
* governance constraints

WITHOUT:

* hidden delegation logic
* unconstrained spawning
* opaque planner behavior

This is NOT "agents deciding randomly."

This is:

* governed contract-based delegation.

---

# REQUIREMENTS

## 1. Add DelegationContract Model

Create:

freya/workflows/contracts.py

Define:

DelegationContract:

* contract_id: str
* parent_session_id: str
* child_session_id: str | None
* delegation_reason: str
* delegated_goal: str
* required_capabilities: list[str]
* expected_outputs: list[str]
* success_criteria: list[str]
* failure_handling: str
* max_iterations: int | None
* max_runtime_seconds: int | None
* governance_constraints: list[str]
* created_at: datetime

Use Pydantic v2.

Generate contract_id via uuid4().

---

## 2. Add Capability Registry Integration

Delegation must validate:

* required capabilities exist

Capability sources:

* ToolRegistry
* PromptCapabilityRegistry

Add helper:

validate_contract_capabilities(contract)

Rules:

* invalid capabilities reject delegation
* validation failures become governance-style events

---

## 3. Add Delegation Approval Policies

Create governance policies:

### ExcessiveDelegationDepthPolicy

Blocks recursive hierarchy explosion.

### MissingCapabilityPolicy

Blocks contracts requiring unavailable capabilities.

### DelegationBudgetPolicy

Blocks workflows exceeding child workflow budget.

Policies integrate with GovernanceEngine.

---

## 4. Extend Subworkflow DAG Format

Current:

{
"task_id": "analyze_logs",
"type": "subworkflow",
"input": {
"goal": "...",
"planning_mode": "cognitive"
}
}

New format:

{
"task_id": "analyze_logs",
"type": "subworkflow",
"input": {
"goal": "...",
"planning_mode": "cognitive",
"contract": {
"delegation_reason": "...",
"required_capabilities": [...],
"expected_outputs": [...],
"success_criteria": [...],
"failure_handling": "...",
"max_iterations": 3,
"governance_constraints": [...]
}
}
}

Contract REQUIRED for subworkflow tasks.

---

## 5. Add Contract Validation Before Spawn

Before child workflow execution:

validate:

* governance policies
* capabilities
* delegation depth
* workflow budgets

If validation fails:

* child NOT spawned
* parent receives summarized observation
* workflow continues safely

---

## 6. Add Delegation Observations

Parent observations should include:

"delegation rejected: missing capability classify_logs"
"subworkflow analyze_logs succeeded under contract"
"subworkflow classify_incident exceeded iteration budget"

Delegation becomes:

* observable
* explainable
* inspectable

---

## 7. Add Contract Persistence

Workflow snapshots must persist:

* active delegation contracts
* child contract lineage

Contracts must survive:

* pause/resume
* restart
* workflow restore

---

## 8. Add Delegation Events

Add events:

delegation_contract_created
delegation_contract_validated
delegation_contract_rejected
delegation_budget_exceeded
delegation_capability_missing

Payload example:

{
"contract_id": "...",
"required_capabilities": ["classify_logs"],
"missing_capabilities": ["classify_logs"]
}

---

## 9. Add Workflow Tree Contract Rendering

Extend:

render_workflow_tree()

Example:

root-workflow
└── analyze_logs
├── contract: log-analysis-v1
├── capabilities: summarize_logs
└── success: produce incident summary

Text rendering only is sufficient.

---

## 10. Add Example Scenarios

Update examples/run_planner.py

Demonstrate:

### Scenario AA — Valid Delegation Contract

* child spawned successfully
* capabilities validated
* contract rendered

### Scenario AB — Missing Capability Rejection

* delegation blocked
* parent observes rejection

### Scenario AC — Delegation Budget Exceeded

* excessive child spawning blocked

### Scenario AD — Contract Persistence

* contract survives pause/resume + restore

Print:

* contracts
* validation events
* governance decisions
* workflow tree with contracts

---

## 11. HARD RULES

DO NOT:

* allow subworkflow spawning without contracts
* allow hidden delegation
* add autonomous peer communication
* add networking
* add distributed systems
* bypass governance policies

Delegation must remain:

* explicit
* governed
* inspectable
* capability-aware

---

## 12. DESIGN INTENT

This step transitions Freya from:

* hierarchical execution

to:

* governed contract-based adaptive delegation

Delegation becomes:

* explainable
* enforceable
* capability-aware
* budget-constrained

This is NOT "AI agents collaborating."

This is:

* explicit governed execution delegation semantics.

---

# OUTPUT FORMAT

Provide:

1. DelegationContract model
2. Governance delegation policies
3. Capability validation
4. Subworkflow contract integration
5. Contract persistence
6. Delegation events
7. Tree rendering updates
8. Updated examples

Do NOT explain.
Only output code.
