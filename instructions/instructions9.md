You are improving an existing Python SDK for an agent execution system.

The system already has:

* ExecutionEngine
* DAGRunner
* Tool system (validated)
* Tracing system
* Policy system
* MemoryStore (session-scoped)
* Worker with pull model
* Transport abstraction

Your task is to HARDEN the system for production safety.

DO NOT rewrite the system. Apply focused improvements.

---

## Fix 1: Session-Level Concurrency Control

Problem:
Multiple workers may execute tasks from the same session concurrently.

### Requirements:

Inside Worker:

* Maintain:
  active_sessions: set[str]

Before executing a task:

* If session_id is already in active_sessions:
  → skip task (do NOT execute)
  → optionally requeue or ignore

* Else:
  → add session_id to active_sessions

After execution:

* remove session_id from active_sessions

---

## Fix 2: Memory Lifecycle Management

Problem:
Memory grows indefinitely per session.

### Requirements:

Add to MemoryStore:

* cleanup_session(session_id: str)

Behavior:

* deletes all keys for that session

---

### Worker Integration:

If task result indicates:

* terminal state (SUCCESS or FAILED for last task)

Then:

* call cleanup_session(session_id)

(If DAG completion is not known, add optional manual cleanup call in example)

---

## Fix 3: Exponential Backoff (Idle Polling)

Problem:
Worker spins with sleep(0.0)

### Requirements:

Implement backoff:

* initial_sleep = 0.1s
* max_sleep = 5s

Logic:

* If no task:
  → sleep_time = min(max_sleep, sleep_time * 2)

* If task found:
  → reset sleep_time to initial_sleep

Use asyncio.sleep()

---

## Fix 4: Idempotent Task Execution

Problem:
Task may be executed multiple times if submission fails.

### Requirements:

Inside Worker:

Maintain:

* executed_tasks: dict[task_id, TaskResult]

Behavior:

* Before execution:
  if task_id in executed_tasks:
  → skip execution
  → resubmit stored result

* After execution:
  → store result in executed_tasks

---

## Fix 5: Structured Error Classification

Problem:
Errors are raw exceptions.

### Requirements:

Update TaskResult:

Add:

* error_type: str (optional)

Map errors:

* Tool not found → "TOOL_NOT_FOUND"
* Validation error → "VALIDATION_ERROR"
* Policy block → "POLICY_BLOCK"
* Execution error → "EXECUTION_ERROR"

Ensure:

* error_type is included in result submission

---

## Fix 6: Safe Memory Logging

Problem:
Large values may flood logs.

### Requirements:

When logging memory events:

* truncate values to max 200 chars
* add flag if truncated

Example:
{
"value": "very long string...",
"truncated": true
}

---

## Constraints

* Do NOT introduce external systems
* Do NOT change public interfaces drastically
* Keep changes minimal and readable
* Maintain async compatibility

---

## Output Format

Provide:

1. Updated Worker code
2. Updated MemoryStore changes
3. Updated TaskResult model
4. Example demonstrating:

   * concurrency safety
   * idempotency
   * backoff behavior

---

## Quality Bar

* No race conditions for session execution
* No infinite memory growth
* No duplicate execution
* Worker remains stable under failures

---

Do NOT explain. Just output code.
