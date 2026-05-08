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
* Delegation contracts
* Capability-aware delegation
* Governance-aware subworkflow spawning
* Workflow trees
* Deterministic and Cognitive planner modes

The architecture is stable and modular.

Your task is to implement:

# Adaptive Execution Strategy System

IMPORTANT:
This step introduces:

* execution strategy selection
* strategy-aware planning
* adaptive runtime decisions
* explicit execution policies
* governed strategy escalation

This step does NOT introduce:

* autonomous swarms
* distributed orchestration
* ML training
* reinforcement learning
* vector databases
* self-modifying planners

Keep implementation:

* deterministic
* inspectable
* governed
* policy-driven

DO NOT rewrite runtime architecture.

ALSO IMPORTANT:
Create a NEW example file instead of extending examples/run_planner.py.

Create:
examples/adaptive_strategy_demo.py

The old file is already too large.

---

# ARCHITECTURE GOAL

Freya currently supports:

* deterministic planning
* cognitive planning
* repair
* recovery
* delegation
* governance checkpoints

BUT:
execution decisions are still hardcoded.

Currently:

* planner mode selected manually
* repair logic static
* delegation static
* HITL static
* recovery static

Now Freya must support:

* adaptive execution strategy selection
* explicit strategy reasoning
* runtime escalation decisions
* strategy policies
* governed strategy transitions

WITHOUT:

* hidden runtime mutations
* autonomous chaos
* opaque execution decisions

This is NOT "agents deciding randomly."

This is:

* governed adaptive execution control.

---

# REQUIREMENTS

## 1. Add ExecutionStrategy Enum

Create:

freya/strategies/models.py

Define:

ExecutionStrategy:

* deterministic
* cognitive
* repair
* recovery
* delegation
* human_approval
* terminate

Use Enum.

---

## 2. Add StrategyDecision Model

Create:

freya/strategies/models.py

Define:

StrategyDecision:

* strategy: ExecutionStrategy
* reason: str
* confidence: float | None
* triggered_by: list[str]
* governance_constraints: list[str]
* created_at: datetime

Use Pydantic v2.

This becomes:

* the explicit execution reasoning object.

---

## 3. Add ExecutionStrategyEngine

Create:

freya/strategies/engine.py

Responsibilities:

* evaluate workflow state
* select next execution strategy
* apply governance constraints
* escalate execution safely

Methods:

select_strategy(
planning_context,
workflow_state,
runtime_signals,
)

Rules:

* deterministic first when possible
* cognitive only when required
* repair only after validation failure
* recovery only after runtime failure
* human_approval only after governance trigger
* terminate when unrecoverable

The engine must be:

* deterministic
* explainable
* inspectable

---

## 4. Add Runtime Signals Model

Create:

freya/strategies/signals.py

Define RuntimeSignals:

* validation_failures
* runtime_failures
* governance_blocks
* delegation_failures
* recovery_attempts
* planner_iterations
* confidence_score
* pending_approvals

Signals become:

* explicit runtime state inputs.

---

## 5. Add Strategy Transition Policies

Create:

freya/strategies/policies.py

Policies:

### MaxRecoveryAttemptsPolicy

Blocks endless recovery loops.

### CognitiveEscalationPolicy

Allows escalation from deterministic → cognitive.

### ForcedHumanApprovalPolicy

Forces HITL after repeated failures.

### TerminationEscalationPolicy

Terminates unrecoverable workflows safely.

Policies integrate with:

* GovernanceEngine
* ExecutionStrategyEngine

---

## 6. Add Strategy Transition Events

Add events:

execution_strategy_selected
execution_strategy_escalated
execution_strategy_blocked
execution_strategy_terminated

Payload example:

{
"from_strategy": "deterministic",
"to_strategy": "cognitive",
"reason": "validation_failures_exceeded"
}

---

## 7. Add Explicit Strategy Trace

Planning trace should now show:

iter=0 strategy=deterministic
iter=1 strategy=repair
iter=2 strategy=recovery
iter=3 strategy=cognitive

Strategy reasoning MUST be visible.

---

## 8. Integrate Into IterativePlannerRunner

Runner should:

* request strategy from ExecutionStrategyEngine
* adapt execution path dynamically
* emit strategy events
* preserve governance enforcement

Current hardcoded branches must become:

* strategy-driven orchestration

DO NOT break:

* persistence
* pause/resume
* event semantics
* workflow coordination

---

## 9. Add Strategy Persistence

Workflow snapshots must persist:

* current execution strategy
* prior strategy decisions
* escalation history

Strategy state must survive:

* pause/resume
* restart
* restore

---

## 10. Add Strategy Visualization

Create helper:

render_strategy_timeline(result)

Example:

iter=0  deterministic  → success
iter=1  repair         → validation fixed
iter=2  recovery       → timeout recovered
iter=3  cognitive      → reasoning required
iter=4  terminate      → unrecoverable

Text-only rendering sufficient.

---

## 11. Create NEW Example File

Create:

examples/adaptive_strategy_demo.py

DO NOT extend run_planner.py.

Demonstrate:

### Scenario A — Deterministic First

* simple execution
* no escalation

### Scenario B — Repair Escalation

* validation failure
* strategy switches to repair

### Scenario C — Runtime Recovery

* timeout
* recovery strategy selected

### Scenario D — Cognitive Escalation

* deterministic insufficient
* escalate to cognitive

### Scenario E — Forced HITL

* repeated failures
* governance forces approval

### Scenario F — Safe Termination

* unrecoverable failure
* terminate strategy selected

### Scenario G — Strategy Persistence

* pause workflow
* restore workflow
* strategy history survives

Print:

* strategy decisions
* escalation reasons
* strategy timeline
* governance interactions

The new example file must remain:

* clean
* modular
* readable

---

## 12. HARD RULES

DO NOT:

* allow hidden strategy changes
* bypass governance
* create autonomous planners
* add distributed execution
* add ML training
* add opaque heuristics

Execution decisions must remain:

* explicit
* inspectable
* governed
* deterministic

---

## 13. DESIGN INTENT

This step transitions Freya from:

* governed workflow execution

to:

* governed adaptive execution control

Execution behavior becomes:

* strategy-aware
* runtime-adaptive
* explainable
* policy-governed

This is NOT autonomous AI.

This is:

* controlled adaptive execution orchestration.

---

# OUTPUT FORMAT

Provide:

1. ExecutionStrategy models
2. Runtime signals
3. Strategy engine
4. Strategy policies
5. Runner integration
6. Strategy persistence
7. Strategy timeline rendering
8. NEW example file: adaptive_strategy_demo.py

Do NOT explain.
Only output code.

Reference inspiration from modern workflow orchestration and adaptive process orchestration systems. ([GitHub][1])

[1]: https://github.com/resources/articles/what-is-workflow-orchestration?utm_source=chatgpt.com "What is Workflow Orchestration?"
