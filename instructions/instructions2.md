You are building a production-grade Python SDK for an agent execution system.

You have already implemented:

* ExecutionEngine (can execute a single task)
* Tool system
* LLM adapter
* Trace capture

Your task is to implement **Step 2: DAG Runner (workflow execution layer)**.

---

## Goal

Build a DAG-based execution system that:

* Executes tasks based on dependencies
* Supports parallel execution where possible
* Integrates with ExecutionEngine
* Handles failures cleanly

This is still LOCAL SDK (no microservices, no persistence).

---

## Requirements

### 1. DAG Data Model

Use Pydantic v2.

Define:

### DAGTask

* task_id: str
* type: Literal["llm", "tool"]
* input: dict
* depends_on: list[str] = []
* config: dict = {}

---

### DAG

* tasks: list[DAGTask]

---

### DAGResult

* results: dict[str, TaskResult]
* status: Literal["SUCCESS", "FAILED"]

---

## 2. DAG Validation

Implement validation before execution:

* Ensure all dependency references exist
* Detect cycles in DAG
* Raise clear error if invalid

You may use:

* networkx OR
* custom topological sort

---

## 3. DAG Runner

Class: DAGRunner

Constructor:

* accepts ExecutionEngine instance

---

### Method:

async run(dag: DAG) -> DAGResult

---

### Execution Behavior:

1. Resolve execution order using topological sorting

2. Execute tasks ONLY when:

   * all dependencies are completed successfully

3. Parallel Execution:

   * Tasks with no dependencies OR whose dependencies are satisfied
   * should run concurrently using asyncio.gather

---

### Dependency Handling:

* Each task receives:

  * its own input
  * PLUS outputs of dependencies (merged into input)

Example:
if task B depends on A:

* B.input = { **B.input, "A": result_of_A }

---

## 4. Failure Handling

* If any task FAILS:

  * Mark DAG as FAILED
  * Do NOT execute dependent tasks
  * Still return partial results

---

## 5. Execution State Tracking

Maintain internal state:

* pending
* running
* completed
* failed

---

## 6. Logging / Debugging

Minimal logging:

* task start
* task completion
* task failure

---

## 7. Async Design

* Fully async
* Efficient scheduling (no busy loops)

---

## Constraints

* Do NOT implement retries
* Do NOT implement FSM/state machine
* Do NOT persist anything
* Do NOT add policy engine
* Do NOT over-engineer

---

## Output Format

Provide:

1. Folder structure updates
2. Full Python code (modular)
3. Example:

* DAG with:

  * Task A (LLM)
  * Task B (tool, depends on A)
  * Task C (LLM, parallel with A)

* Run DAG and print results

---

## Quality Bar

* Clean dependency resolution
* Correct parallel execution
* No race conditions
* No unnecessary abstractions

---

Do NOT explain. Just output code.
