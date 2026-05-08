You are fixing a bug in a Python SDK worker system.

The current issue:
Memory is being cleaned up prematurely because the worker assumes a session is complete when no active tasks remain.

This assumption is incorrect because:

* tasks are fetched dynamically
* worker cannot know if more tasks will arrive

---

## Fix Requirements

### 1. REMOVE incorrect logic

Remove:

* session_active_tasks tracking
* cleanup based on active_tasks == 0

---

### 2. Introduce safe cleanup strategy (choose one)

Implement BOTH:

---

### (A) TTL-based cleanup

* Track last_access_time per session
* If session inactive for N seconds (e.g. 60s):
  → cleanup memory

---

### (B) Optional terminal signal

If fetched task contains:

* "is_terminal": true

Then:

* cleanup immediately after execution

---

### 3. Update Worker logic

* Do NOT assume session completion
* Only cleanup based on:

  * TTL
  * terminal flag

---

### 4. Logging

When cleanup happens:

* log reason:
  "memory_cleanup", session_id, reason="ttl" or "terminal"

---

### 5. Example update

Demonstrate:

* two tasks in same session
* memory persists correctly
* cleanup happens AFTER TTL or terminal flag

---

## Constraints

* No control plane yet
* Keep solution simple and safe
* Do NOT reintroduce premature cleanup

---

Do NOT explain. Just output code.
