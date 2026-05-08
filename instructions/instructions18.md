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
* Memory layer
* Trace system
* Capability-aware planning
* Observation summaries
* Deterministic and Cognitive planner modes

The architecture is stable and modular.

Your task is to implement:

# Validation + Repair Loop

IMPORTANT:
This is NOT a self-modifying autonomous system.

The goal is:

* bounded adaptive recovery
* DAG validation
* targeted repair
* deterministic failure handling

DO NOT rewrite runtime architecture.

---

# ARCHITECTURE GOAL

Planner-generated DAG fragments must now:

1. be validated BEFORE execution
2. produce structured validation failures
3. allow planner-driven repair attempts
4. retry ONLY failed DAG fragments
5. remain bounded and deterministic

This transitions Freya from:

* observation-aware planning

to:

* resilient adaptive orchestration

---

# REQUIREMENTS

## 1. Add ValidationError model

Create:

freya/planner/validation.py

Define:

ValidationIssue:

* issue_type: str
* message: str
* task_id: str | None
* offending_value: str | None

ValidationResult:

* valid: bool
* issues: list[ValidationIssue]

Use Pydantic v2.

---

## 2. Add DAG Validator

Create:

validate_dag_fragment(
dag,
tool_registry,
planning_context,
) -> ValidationResult

Validation must check:

* DAG schema correctness
* duplicate task IDs
* tool existence
* dependency validity
* cycles
* invalid task types
* missing required fields

DO NOT execute tasks during validation.

---

## 3. Add RepairObservation

Extend Observation:

repair_attempted: bool = False
repair_reason: str | None = None

---

## 4. Add Repair Loop to IterativePlannerRunner

Planner execution loop becomes:

1. planner generates DAG fragment
2. validate fragment
3. if valid:
   execute fragment
4. if invalid:
   create repair observation
   ask planner to repair fragment
   validate repaired fragment
5. if still invalid:
   terminate safely

---

## 5. Repair Attempt Limits

Add hard limits:

MAX_REPAIR_ATTEMPTS = 1

DO NOT allow infinite repair loops.

---

## 6. Planner Repair Prompting

When validation fails:

Planner receives:

Validation issues:

* Tool 'write_values' does not exist
* Task 'x' has invalid dependency

Recent observations:
...

Repair the DAG fragment.
Return ONLY corrected DAG JSON.

Planner should repair ONLY failed fragment.

DO NOT regenerate entire workflow.

---

## 7. Trace Integration

Add trace events:

planner_validation_failed
planner_repair_attempted
planner_repair_succeeded
planner_repair_failed

Example payloads:

{
"issues": [...]
}

{
"repair_attempt": 1
}

---

## 8. Observation Integration

Repair failures should become observations.

Example summary:

"planner generated invalid DAG because tool 'write_values' does not exist"

Planner should be able to reason over repair history.

---

## 9. Example

Update examples/run_planner.py

Demonstrate BOTH:

### Successful repair

Planner initially generates:

* invalid tool name

Validator rejects it.

Planner repairs:

* corrected tool name

Execution succeeds.

---

### Failed repair

Planner generates invalid DAG twice.

Runner terminates safely.

Print:

* validation issues
* repair attempts
* repair outcomes

---

## 10. HARD RULES

DO NOT:

* regenerate full workflow during repair
* allow unbounded repair loops
* execute invalid DAGs
* mutate existing successful tasks
* couple validator to execution engine internals

Repair must remain:

* local
* bounded
* deterministic

---

## 11. DESIGN INTENT

This step transitions Freya from:

* adaptive planning

to:

* resilient adaptive cognition

The planner should now:

* recognize invalid plans
* repair broken fragments
* continue execution safely

without destabilizing the runtime.

---

# OUTPUT FORMAT

Provide:

1. Validation models
2. DAG validator
3. Repair loop integration
4. Observation updates
5. Trace updates
6. Updated planner prompts
7. Updated examples

Do NOT explain.
Only output code.
