You are fixing a bug in a Python SDK worker system.

The issue:
Memory is not persisting across tasks in the same session.

Observed behavior:

* Task A stores value in memory
* Task B (same session) retrieves None

This is incorrect.

---

## Requirements

### 1. Ensure Shared MemoryStore

Worker must have ONE memory store:

self._memory = InMemoryStore()

---

### 2. ExecutionContext must reuse same memory

When executing each task:

context = ExecutionContext(
session_id=task["session_id"],
task_id=task["task_id"],
memory=self._memory   # MUST reuse
)

---

### 3. DO NOT create new MemoryStore per task

Remove any code like:

memory = InMemoryStore()

inside execution loop

---

### 4. Ensure session_id consistency

* Use exact session_id from fetched task
* Do not modify / trim / reformat

---

### 5. Verify Tool Integration

Ensure tools receive context:

async def execute(self, input, context):

and use:

context.memory.get(context.session_id, key)

---

### 6. Add Debug Logging

Temporarily log:

* memory keys before and after each task

Example:
log("memory_keys", session_id, keys=list_keys)

---

### 7. Example Validation

Run:

* Task A: store ("greeting", "hello")
* Task B: get ("greeting")

Expected output:
{"value": "hello"}

---

## Constraints

* Do NOT change lifecycle logic
* Do NOT change cleanup logic
* Fix only memory propagation

---

Do NOT explain. Just output code.
