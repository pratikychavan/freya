You are building a production-grade Python SDK for an agent execution system.

Your task is to implement **Step 1: Execution Engine (core runtime)**.

## Goal

Build a clean, extensible execution engine that can:

* Execute LLM tasks
* Execute Python function tools
* Capture structured traces
* Be async-first

This is a LOCAL SDK (no microservices, no networking).

---

## Requirements

### 1. Define Core Data Models

Use Pydantic v2.

Define:

### Task

* task_id: str
* type: Literal["llm", "tool"]
* input: dict
* config: dict (optional)

### TaskResult

* task_id: str
* status: Literal["SUCCESS", "FAILED"]
* output: dict | None
* error: str | None
* duration_ms: int

---

### 2. Define LLM Adapter Interface

Use Python Protocol.

Interface:

* async complete(request: dict) -> dict
* async stream(request: dict) -> AsyncIterator[str]
* supports_vision() -> bool
* supports_tool_calls() -> bool
* token_budget() -> int

---

### 3. Implement OpenAI Adapter

* Use openai-python SDK
* Only support simple completion (no streaming for now)
* Input:
  {
  "prompt": str,
  "model": str
  }
* Output:
  {
  "text": str,
  "usage": dict
  }

---

### 4. Tool Interface

Define base Tool class:

* name: str
* input_schema: dict
* output_schema: dict

Method:

* async execute(input: dict) -> dict

---

### 5. Execution Engine

Class: ExecutionEngine

Method:

* async execute_task(task: Task) -> TaskResult

Behavior:

IF task.type == "llm":

* Call LLM adapter
* Pass input directly

IF task.type == "tool":

* Lookup tool from registry
* Validate input using jsonschema
* Execute tool
* Validate output

---

### 6. Tool Registry (in-memory)

* register_tool(tool)
* get_tool(name)

---

### 7. Trace Capture

Create Trace class:

Must capture:

* task_id
* start_time
* end_time
* input
* output
* error (if any)
* token_usage (if LLM)

Trace must be returned as part of execution result (or attached cleanly).

---

### 8. Error Handling

* Catch all exceptions
* Return structured TaskResult (never crash)
* Include error message

---

### 9. Async Design

* Everything must be async
* Use asyncio

---

## Constraints

* No microservices
* No database
* No Redis
* No orchestration/DAG yet
* No policy engine yet
* No retries yet

Keep it minimal but clean.

---

## Output Format

Provide:

1. Clean folder structure
2. Full Python code (modular, not one file)
3. Example usage:

* Register a sample tool
* Run:

  * one LLM task
  * one tool task

---

## Quality Bar

* Production-level structure (not toy script)
* Clean typing
* No unnecessary abstractions
* No over-engineering

---

Do NOT explain. Just output code.
