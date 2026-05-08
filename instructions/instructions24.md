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
* ToolRegistry
* PromptRegistry
* PromptCapabilityRegistry
* PlanningMode
* Memory layer
* Trace system
* Deterministic and Cognitive planner modes

The architecture is stable and modular.

Your task is to implement:

# Internal Event-Driven Runtime Architecture

IMPORTANT:
This step introduces:

* runtime event bus
* lifecycle subscribers
* event hooks
* decoupled telemetry/governance hooks
* internal reactive runtime architecture

This step does NOT introduce:

* Kafka
* Redis
* external message brokers
* distributed event streaming
* networking
* microservices

Keep implementation:

* in-process
* deterministic
* lightweight
* observable

DO NOT rewrite runtime architecture.

---

# ARCHITECTURE GOAL

Freya currently:

* directly emits traces
* directly invokes governance
* directly performs persistence

This creates increasing orchestration coupling.

Now Freya must support:

* internal event publication
* runtime subscribers
* decoupled lifecycle handling
* pluggable orchestration hooks

WITHOUT:

* introducing distributed complexity
* breaking deterministic execution
* mutating workflow semantics

This is NOT distributed event streaming.

This is:

* internal runtime event architecture.

---

# REQUIREMENTS

## 1. Add RuntimeEvent Model

Create:

freya/events/models.py

Define:

RuntimeEvent:

* event_id: str
* event_type: str
* session_id: str
* workflow_state: str | None
* iteration: int | None
* timestamp: datetime
* payload: dict

Use Pydantic v2.

Generate event_id via uuid4().

---

## 2. Add EventSubscriber Protocol

Create:

freya/events/base.py

Define:

class EventSubscriber(Protocol):

```
async def handle_event(
    self,
    event: RuntimeEvent,
) -> None:
    ...
```

Subscribers MUST:

* never mutate runtime state directly
* never block indefinitely
* remain side-effect isolated

---

## 3. Add InProcessEventBus

Create:

freya/events/bus.py

Responsibilities:

* register subscribers
* publish events
* fan out events to subscribers
* isolate subscriber failures

Methods:

* subscribe(subscriber)
* publish(event)

Rules:

* subscribers invoked sequentially
* subscriber exceptions MUST NOT crash runtime
* failures become trace events

---

## 4. Add Built-In Subscribers

Create:

freya/events/subscribers.py

Implement:

### TraceSubscriber

Converts RuntimeEvents into trace entries.

### PersistenceSubscriber

Automatically persists workflow snapshots when:

* workflow paused
* workflow resumed
* workflow completed

### GovernanceAuditSubscriber

Records governance-related lifecycle events.

Subscribers MUST remain modular.

---

## 5. Replace Direct Trace Emission

Update:

* IterativePlannerRunner
* GovernanceEngine
* PersistentWorkflowStore

Replace direct trace insertion with:

* RuntimeEvent publication

TraceSubscriber becomes responsible for:

* trace creation

---

## 6. Add Event Types

Standardize event names.

Examples:

planner_iteration_started
planner_iteration_completed
workflow_paused_for_approval
workflow_resumed_after_approval
workflow_completed
workflow_failed
workflow_snapshot_persisted
workflow_lease_acquired
workflow_version_conflict
governance_evaluated
runtime_failure_observed

Use constants/enums where appropriate.

---

## 7. Add Event Replay Buffer

Add optional in-memory replay buffer.

Capabilities:

* last N events retrievable
* debugging support
* observability support

Methods:

* recent_events(limit=50)

DO NOT persist replay buffer yet.

---

## 8. Add Subscriber Failure Isolation

If subscriber crashes:

* runtime continues
* subscriber failure event emitted
* event handling remains deterministic

Add event:

subscriber_failure

Payload:

* subscriber_name
* error

---

## 9. Update Examples

Update examples/run_planner.py

Demonstrate:

### Scenario T — Event Stream

Print emitted runtime events in order.

### Scenario U — Subscriber Failure Isolation

Add a subscriber that intentionally crashes.
Verify:

* workflow still completes
* subscriber_failure event emitted

### Scenario V — Persistence Subscriber

Verify workflow snapshot persisted automatically through events.

Print:

* ordered event stream
* subscriber activity
* replay buffer contents

---

## 10. HARD RULES

DO NOT:

* add Kafka
* add Redis
* add threads
* add multiprocessing
* add networking
* add distributed systems
* allow subscribers to mutate runtime internals

Events must remain:

* local
* deterministic
* observable
* append-only

---

## 11. DESIGN INTENT

This step transitions Freya from:

* directly orchestrated runtime

to:

* event-driven governed cognition runtime

Runtime behavior becomes:

* composable
* observable
* extensible
* loosely coupled

WITHOUT introducing distributed infrastructure.

This is foundational reactive runtime architecture.

---

# OUTPUT FORMAT

Provide:

1. RuntimeEvent model
2. Event bus implementation
3. Subscribers
4. Runner integration
5. Event replay buffer
6. Subscriber isolation
7. Updated examples

Do NOT explain.
Only output code.
