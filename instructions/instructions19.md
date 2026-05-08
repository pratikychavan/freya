You are working inside the Freya SDK repository.

Freya already supports:

* ExecutionEngine
* DAGRunner
* IterativePlannerRunner
* PlanningContext
* Observation-aware planning
* ToolRegistry
* PromptRegistry
* PromptCapabilityRegistry
* PlanningMode
* Validation + Repair loop
* Memory layer
* Trace system
* Capability-aware planning
* Observation summaries
* Deterministic and Cognitive planner modes

The architecture is stable and modular.

Your task is to implement:

# Runtime Failure Recovery

IMPORTANT:
This is NOT autonomous self-healing AI.

The goal is:

* bounded runtime recovery
* selective retry
* execution-aware repair
* adaptive downstream correction

DO NOT rewrite runtime architecture.

---

# ARCHITECTURE GOAL

Freya currently repairs:

* invalid DAG fragments BEFORE execution

Now Freya must also recover from:

* runtime task failures DURING execution

Examples:

* tool exceptions
* timeout failures
* invalid outputs
* policy rejection
* LLM execution failure

Planner should:

* observe runtime failure
* reason about failure
* generate targeted recovery DAG fragment
* continue safely when possible

WITHOUT:

* regenerating entire workflow
* mutating successful tasks
* entering infinite retries

---

# REQUIREMENTS

## 1. Extend Observation Model

Update:

freya/planner/observation.py

Add:

failure_category: str | None = None
recoverable: bool = False
recovery_attempted: bool = False

Examples:

* TOOL_EXCEPTION
* TIMEOUT
* POLICY_BLOCK
* INVALID_OUTPUT
* LLM_FAILURE

---

## 2. Failure Classification

Create:

freya/planner/failure_classifier.py

Define:

classify_failure(error) -> dict

Returns:
{
"failure_category": "...",
"recoverable": bool,
"summary": "..."
}

Examples:

KeyError → recoverable=True
TimeoutError → recoverable=True
PolicyBlock → recoverable=False

Keep implementation deterministic and rule-based.

DO NOT use LLM classification.

---

## 3. Runtime Failure Observation Integration

When task execution fails:

Create Observation:

* status="FAILED"
* failure_category
* recoverable
* semantic_summary

Example summary:

"query_database failed due to timeout"

Store inside PlanningContext.recent_observations.

---

## 4. Recovery Planning Loop

Update IterativePlannerRunner.

New behavior:

If task failure is recoverable:

* planner receives failure observation
* planner generates recovery DAG fragment
* execute recovery fragment
* continue workflow

If failure is NOT recoverable:

* terminate safely

---

## 5. Recovery Limits

Add hard limits:

MAX_RUNTIME_RECOVERY_ATTEMPTS = 2

Track recovery count per task.

DO NOT allow infinite retries.

---

## 6. Planner Recovery Prompting

Planner prompt must now include:

Recoverable runtime failures:

* query_database failed due to timeout

Determine:

* retry
* alternate tool
* fallback cognition capability
* safe termination

Planner should repair ONLY affected execution path.

DO NOT regenerate successful tasks.

---

## 7. Recovery Trace Events

Add:

runtime_failure_observed
runtime_recovery_attempted
runtime_recovery_succeeded
runtime_recovery_failed
runtime_failure_terminal

Example payloads:

{
"task_id": "query_database",
"failure_category": "TIMEOUT",
"recoverable": true
}

---

## 8. Recovery Strategies

Planner may:

* retry task
* select alternate tool
* invoke summarize_logs capability
* branch workflow
* terminate safely

Planner MUST NOT:

* mutate completed successful tasks
* clear memory
* restart workflow

---

## 9. Example Tools

Create failing example tools:

### FlakyTool

* fails first execution
* succeeds second execution

### FatalTool

* always raises unrecoverable exception

---

## 10. Example Scenarios

Update examples/run_planner.py

Demonstrate:

### Scenario A — Recoverable failure

* task fails initially
* failure observation created
* planner retries
* workflow succeeds

### Scenario B — Unrecoverable failure

* fatal failure observed
* planner terminates safely

Print:

* failure observations
* recovery attempts
* recovery outcomes

---

## 11. HARD RULES

DO NOT:

* regenerate entire workflow
* retry indefinitely
* mutate successful tasks
* expose raw stack traces to planner
* create recursive repair loops

Recovery must remain:

* bounded
* local
* deterministic
* observable

---

## 12. DESIGN INTENT

This step transitions Freya from:

* validation-aware orchestration

to:

* execution-resilient orchestration

Planner should now:

* adapt to runtime failures
* recover selectively
* continue safely

while preserving deterministic execution boundaries.

---

# OUTPUT FORMAT

Provide:

1. Observation updates
2. Failure classifier
3. Recovery loop integration
4. Recovery traces
5. Updated planner prompts
6. Example tools
7. Updated examples

Do NOT explain.
Only output code.
