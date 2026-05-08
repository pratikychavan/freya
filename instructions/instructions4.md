You are building a production-grade Python SDK for an agent execution system.

You have already implemented:

* ExecutionEngine (task execution)
* DAGRunner (workflow execution)
* Tool system with strict schema validation

Your task is to implement **Step 4: Tracing System (observability layer)**.

---

## Goal

Build a structured tracing system that:

* Captures full execution lifecycle of each task
* Works across DAG execution
* Is easy to export and debug
* Has zero external dependencies (no OpenTelemetry yet)

---

## Requirements

### 1. Trace Data Models

Use Pydantic v2.

Define:

### TraceEvent

* event_id: str
* timestamp: float
* event_type: Literal[
  "task_started",
  "task_completed",
  "task_failed",
  "llm_call_started",
  "llm_call_completed",
  "tool_call_started",
  "tool_call_completed"
  ]
* task_id: str
* payload: dict

---

### TaskTrace

* task_id: str
* start_time: float
* end_time: float | None
* status: Literal["SUCCESS", "FAILED"]
* events: list[TraceEvent]
* error: str | None
* token_usage: dict | None

---

### DAGTrace

* session_id: str
* task_traces: dict[str, TaskTrace]
* start_time: float
* end_time: float | None
* status: Literal["SUCCESS", "FAILED"]

---

## 2. Trace Manager

Class: TraceManager

Responsibilities:

* create and store traces
* append events
* finalize traces

Methods:

* start_task(task_id)
* log_event(task_id, event_type, payload)
* complete_task(task_id, status, error=None, token_usage=None)
* get_task_trace(task_id)
* export_dag_trace()

---

## 3. ExecutionEngine Integration

Update ExecutionEngine:

For each task:

* call start_task()
* log:

  * task_started
  * llm_call_started / tool_call_started
  * llm_call_completed / tool_call_completed
  * task_completed or task_failed

---

## 4. DAGRunner Integration

* Initialize DAGTrace at start
* Pass TraceManager to ExecutionEngine
* Update DAG status based on results
* finalize DAG trace

---

## 5. Timing

* Use time.time() for timestamps
* Compute duration from start/end

---

## 6. Error Handling

* Errors must be recorded in trace
* Even failed tasks must produce a valid TaskTrace

---

## 7. Export

Implement:

trace_manager.export_dag_trace()

Returns:

* fully serializable dict (JSON-ready)

---

## 8. Example

Provide example:

* Run DAG with:

  * one successful task
  * one failing task

* Print exported trace

---

## Constraints

* No external tracing libraries
* No async logging frameworks
* No file storage (in-memory only)

---

## Output Format

Provide:

1. Updated folder structure
2. Full Python code
3. Example usage showing trace output

---

## Quality Bar

* Clean event structure
* No missing events
* Easy to debug from trace alone
* No over-engineering

---

Do NOT explain. Just output code.
