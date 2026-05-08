You are improving an existing Python SDK for an agent execution system.

The system already has:

* ExecutionEngine
* DAGRunner
* Tool system (Pydantic validated)
* Trace system
* Policy system

Your task is to FIX issues in the Policy Layer implementation.

DO NOT rewrite everything. Modify existing logic cleanly.

---

## Problems to Fix

### 1. Missing Policy Attribution in Trace (CRITICAL)

Currently trace logs show:
[input] ALLOW
[input] WARN

This is insufficient.

### Fix:

Every policy evaluation MUST include:

* policy_name
* action
* reason

Update trace events to include:

{
"policy_name": str,
"action": "ALLOW" | "BLOCK" | "WARN",
"reason": str | None
}

Ensure this is visible in:

* input checks
* output checks

---

### 2. No Short-Circuit on BLOCK (CRITICAL)

Currently all policies are evaluated even after a BLOCK.

### Fix:

Update PolicyManager:

* Evaluate policies sequentially
* If any policy returns BLOCK:
  → immediately STOP evaluation
  → return results collected so far

Behavior:

for policy in policies:
result = policy.check()

```
log result

if result.action == "BLOCK":
    break
```

---

### 3. Output Policies Executed After Input BLOCK (CRITICAL)

If input is BLOCK:

* Task execution must NOT happen
* Output policies must NOT run

### Fix ExecutionEngine:

Flow must be:

1. Evaluate input policies

2. IF BLOCK:

   * return FAILED TaskResult immediately
   * skip execution
   * skip output policies

3. ELSE:

   * execute task
   * evaluate output policies

---

### 4. Clean Trace Integration

For every policy check, log:

event_type = "policy_check"

payload must include:

* stage: "input" | "output"
* policy_name
* action
* reason

---

### 5. Ensure No Duplicate Evaluations

* Each policy must run exactly once per stage
* No repeated ALLOW entries without context

---

## Constraints

* Do NOT change public interfaces unnecessarily
* Do NOT introduce new frameworks
* Keep implementation minimal and clean
* Maintain async compatibility

---

## Output Format

Provide:

1. Updated PolicyManager code
2. Updated ExecutionEngine policy integration
3. Updated trace logging changes
4. Small example showing:

   * one BLOCK case
   * one WARN case
   * trace output with policy names

---

## Quality Bar

* No redundant evaluations
* Clear trace attribution
* Strict BLOCK enforcement
* Minimal code changes (surgical fix)

---

Do NOT explain. Just output code.
