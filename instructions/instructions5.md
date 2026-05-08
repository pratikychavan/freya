You are building a production-grade Python SDK for an agent execution system.

You have already implemented:

* ExecutionEngine (task execution)
* DAGRunner (workflow execution)
* Tool system with strict schema validation
* Tracing system

Your task is to implement **Step 5: Policy Layer (lightweight, pluggable guardrails)**.

---

## Goal

Build a simple but extensible policy system that:

* Runs checks BEFORE and AFTER task execution
* Can BLOCK or WARN
* Is easy to extend later
* Integrates with ExecutionEngine and DAGRunner

---

## Requirements

### 1. Policy Result Model

Use Pydantic v2.

Define:

PolicyResult:

* action: Literal["ALLOW", "BLOCK", "WARN"]
* reason: str | None

---

### 2. Policy Base Class

Define abstract class:

Policy:

Methods:

* check_input(task: dict, context: dict) -> PolicyResult
* check_output(task: dict, result: dict, context: dict) -> PolicyResult

---

### 3. Policy Manager

Class: PolicyManager

Responsibilities:

* hold list of policies
* evaluate all policies

Methods:

* add_policy(policy)
* evaluate_input(task, context) -> list[PolicyResult]
* evaluate_output(task, result, context) -> list[PolicyResult]

---

### 4. Policy Execution Rules

When evaluating:

* If ANY policy returns BLOCK:
  → stop execution immediately

* If WARN:
  → log but continue

* If all ALLOW:
  → proceed

---

### 5. Example Policies

Implement at least TWO:

---

### (A) MaxLengthPolicy

* Applies to LLM tasks
* If input["prompt"] length > threshold:
  → BLOCK

---

### (B) RequiredFieldPolicy

* Applies to tool tasks
* Ensure specific keys exist in input
* If missing:
  → BLOCK

---

### 6. ExecutionEngine Integration

Update execution flow:

### BEFORE execution:

* call policy_manager.evaluate_input()
* if BLOCK:

  * do NOT execute task
  * return FAILED TaskResult

---

### AFTER execution:

* call policy_manager.evaluate_output()
* if BLOCK:

  * mark task FAILED

---

### WARN:

* log warning via trace system

---

## 7. DAGRunner Integration

* Ensure blocked tasks:

  * are marked FAILED
  * dependent tasks are NOT executed

---

## 8. Context Support

Policies must receive context:

Example:
{
"session_id": "...",
"task_id": "...",
"task_type": "llm" | "tool"
}

---

## 9. Logging

* All policy decisions must be logged in trace events:

  * event_type: "policy_check"
  * include action + reason

---

## 10. Example Usage

* Register policies

* Run DAG with:

  * one allowed task
  * one blocked task
  * one warning case

* Show:

  * execution results
  * trace output with policy events

---

## Constraints

* No YAML policy config
* No LLM-based policies
* No external services
* Keep everything in-memory

---

## Output Format

Provide:

1. Updated folder structure
2. Full Python code
3. Example usage

---

## Quality Bar

* Clean integration with engine
* Clear separation of concerns
* Easy to extend later
* No over-engineering

---

Do NOT explain. Just output code.
