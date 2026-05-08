You are working inside the Freya SDK repository.

Freya is a production-oriented agent runtime system with:

* ExecutionEngine
* DAGRunner
* Tool Registry
* Policy Layer
* Trace System
* Memory Layer
* Worker Runtime
* Prompt Registry

The runtime is already deterministic and stable.

Your task is to implement the FIRST VERSION of an iterative planner system.

IMPORTANT:
This is NOT a free-form autonomous agent.
This is a bounded, controlled DAG expansion system.

The planner MUST:

* generate partial DAGs
* observe execution results
* iteratively expand workflow
* remain deterministic and debuggable

DO NOT rewrite existing architecture.

---

# GOAL

Implement:

IterativePlanner

which supports:

Goal
→ generate partial DAG
→ execute
→ observe results
→ generate next DAG frontier
→ continue until terminal condition

---

# ARCHITECTURE REQUIREMENTS

## 1. Planner MUST NOT execute tasks directly

Planner responsibilities:

* synthesize DAG nodes
* analyze runtime outputs
* decide next steps

Execution responsibilities remain:

* ExecutionEngine
* DAGRunner

---

## 2. Add PlanningContext

Create:

freya/planner/context.py

Model:

PlanningContext:

* session_id: str
* goal: str
* completed_tasks: list[str]
* failed_tasks: list[str]
* task_results: dict
* memory_snapshot: dict
* trace_summary: dict
* iteration_count: int

Use Pydantic v2.

---

## 3. Add Planner Interface

Create:

freya/planner/base.py

Define:

class BasePlanner(ABC):

```
async def plan_next(
    self,
    context: PlanningContext
) -> DAG:
    ...
```

Planner returns ONLY:

* new DAG fragment
* no execution

---

## 4. Implement SimpleIterativePlanner

Create:

freya/planner/simple.py

Behavior:

* Uses PromptRegistry
* Uses LLM adapter
* Generates partial DAG JSON

Input:

* current PlanningContext

Output:

* DAG fragment

---

## 5. STRICT DAG GENERATION RULES

Planner output MUST:

* reference existing tools only
* produce valid DAG schema
* avoid cycles
* keep DAG minimal

---

## 6. Add Validation Layer

Before executing generated DAG:

Validate:

* schema correctness
* tool existence
* dependency correctness

If invalid:

* planner retries once
* if still invalid → FAIL safely

DO NOT allow invalid DAG execution.

---

## 7. Add IterativePlannerRunner

Create:

freya/planner/runner.py

Responsibilities:

Loop:

1. planner.plan_next()
2. validate DAG
3. execute DAG fragment
4. update PlanningContext
5. repeat

Stop conditions:

* planner returns empty DAG
* max_iterations reached
* fatal failure
* explicit terminal signal

---

## 8. HARD SAFETY LIMITS (MANDATORY)

Add:

MAX_ITERATIONS = 10
MAX_TOTAL_TASKS = 50
MAX_REPAIR_ATTEMPTS = 1

Planner MUST stop safely.

No infinite loops.

---

## 9. TRACE INTEGRATION

Trace:

* planning step
* generated DAG
* validation errors
* repair attempts
* termination reason

Add event types:

* planner_iteration
* planner_validation_failed
* planner_terminated

---

## 10. MEMORY INTEGRATION

Planner must receive:

* memory snapshot
* recent task outputs

Planner may use memory to decide next DAG fragment.

Planner MUST NOT mutate memory directly.

---

## 11. EXAMPLE

Provide working example:

Goal:
"Store number 10, retrieve it, and explain the retrieved value."

Expected behavior:

* planner creates first DAG fragment
* runtime executes
* planner observes result
* planner creates next DAG fragment
* planner terminates

Use MockLLMAdapter if needed.

---

## 12. CONSTRAINTS

DO NOT:

* implement recursive self-calling agents
* implement ReAct loops
* allow direct tool execution from planner
* mutate runtime architecture unnecessarily
* introduce external dependencies

Keep implementation:

* modular
* deterministic
* bounded
* production-readable

---

# OUTPUT FORMAT

Provide:

1. Folder structure updates
2. Full Python code
3. Example iterative planning flow
4. Validation + repair logic
5. Trace integration

Do NOT explain.
Only output code.
