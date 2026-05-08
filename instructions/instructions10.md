You are improving an existing Python SDK for an agent execution system.

The system already includes:

* ExecutionEngine
* DAGRunner
* Tool system (validated)
* Tracing system
* Policy system
* MemoryStore (session-scoped)
* Worker (pull model, idempotent, backoff implemented)
* Transport abstraction

Your task is to FIX remaining production risks related to:

* session lifecycle
* multi-worker safety
* memory cleanup correctness

DO NOT rewrite the system. Apply focused fixes.

---

## Fix 1: Explicit Session Lifecycle Tracking

Problem:
Worker does not know when a session is complete.

### Requirements:

Introduce session tracking inside Worker:

* session_task_counts: dict[session_id, int]
* session_active_tasks: dict[session_id, int]

Behavior:

When task fetched:

* increment session_active_tasks[session_id]

When task completes (SUCCESS or FAILED):

* decrement session_active_tasks[session_id]

When:

* session_active_tasks[session_id] == 0
  → session is COMPLETE

---

## Fix 2: Safe Memory Cleanup

Problem:
Memory cleanup may happen too early or never.

### Requirements:

When session is COMPLETE:

* call memory.cleanup_session(session_id)
* remove session tracking entries

Ensure:

* cleanup happens exactly once
* no race condition

---

## Fix 3: Multi-Worker Session Lock (Local Safety)

Problem:
Multiple workers may process same session concurrently.

### Requirements:

Inside Worker:

Maintain:

* active_sessions: set[str]

Before execution:

* if session_id in active_sessions:
  → skip task (do not execute)
  → optionally requeue or delay

* else:
  → add session_id to active_sessions

After execution:

* remove session_id

---

## Fix 4: Session-Level Backoff (Optional but preferred)

Enhance backoff:

Instead of only global backoff:

* track per-session temporary skip

Example:

* if session locked → small delay before retry

---

## Fix 5: Memory Cleanup Verification

Add logging:

When cleanup occurs:

* log:
  "memory_cleanup", session_id

Ensure:

* after cleanup, list_keys(session_id) returns empty list

---

## Fix 6: Defensive Idempotency Note

Document clearly in code:

* executed_tasks cache is in-memory only
* persistence is required in control plane later

Add comments (no implementation required)

---

## Example Update

Provide updated example:

* simulate multiple tasks for same session
* show:

  * tasks processed sequentially
  * session completes
  * memory cleaned
  * cleanup log visible

---

## Constraints

* No database
* No distributed locks
* No external services
* Keep implementation minimal and correct

---

## Output Format

Provide:

1. Updated Worker code
2. Updated MemoryStore changes (if any)
3. Example demonstrating:

   * session completion
   * memory cleanup
   * no parallel execution for same session

---

## Quality Bar

* No memory leaks
* No concurrent execution per session
* Clean lifecycle handling
* Minimal changes, no over-engineering

---

Do NOT explain. Just output code.
