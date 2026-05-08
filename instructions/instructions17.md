You are working inside the Freya SDK repository.

Freya already supports:

* ExecutionEngine
* DAGRunner
* IterativePlannerRunner
* PlanningContext
* ToolRegistry
* PromptRegistry
* PromptCapabilityRegistry
* PlanningMode (deterministic / cognitive)
* Memory layer
* Trace system
* Capability-aware planning

The architecture is already stable and modular.

Your task is to implement:

# Observation-Aware Planning

IMPORTANT:
This is NOT a self-reflective autonomous agent system.

The goal is:

* state-driven planning
* observation-aware DAG synthesis
* adaptive iterative orchestration

DO NOT rewrite runtime architecture.

---

# ARCHITECTURE GOAL

Currently planner behavior is effectively iteration-driven.

We want planner decisions to derive from:

* runtime observations
* recent task outputs
* failures
* memory summaries
* semantic execution state

instead of:

* iteration number
* hardcoded sequencing

---

# REQUIREMENTS

## 1. Add Observation Model

Create:

freya/planner/observation.py

Define:

Observation:

* task_id: str
* task_type: str
* status: str
* output: dict | None
* error: str | None
* timestamp: datetime
* semantic_summary: str | None

Use Pydantic v2.

---

## 2. Extend PlanningContext

Add:

recent_observations: list[Observation]

Add helper methods:

* latest_success()
* latest_failure()
* summarize_observations()

summarize_observations() should:

* produce compact planner-friendly summaries
* avoid large raw dumps

Example summary:

[
"retrieve_value succeeded and returned value=10",
"store_value wrote key=my_number"
]

---

## 3. Observation Collection

Update IterativePlannerRunner.

After each task execution:

* create Observation
* append to PlanningContext

Observation must include:

* task output
* task failure
* timestamp

DO NOT store raw traces inside observations.

---

## 4. Semantic Observation Compression

Add utility:

freya/planner/context_builder.py

Responsibilities:

* compress planner context
* select relevant observations
* prevent prompt bloat

Create:

build_planner_context(context: PlanningContext) -> dict

Output should include:

* goal
* planning_mode
* recent_observation_summaries
* memory_summary
* available_tools
* available_prompt_capabilities

DO NOT include:

* raw traces
* entire memory dump
* irrelevant task history

---

## 5. Planner Prompt Rewrite

Update planner prompt generation.

The planner prompt MUST now include:

Recent observations:

* retrieve_value succeeded and returned value=10
* store_value wrote key=my_number

The planner should determine next DAG fragment based on observations.

Planner MUST NOT rely on:

* iteration count
* hardcoded execution order

---

## 6. Adaptive Planning Behavior

Planner decisions should now derive from observations.

Example:

If:

* retrieve_value returned value=10
  AND:
* explain_number capability exists

Planner may generate:

* explain_value task

This should happen because of runtime observations,
NOT because iteration == 2.

---

## 7. Trace Integration

Add trace events:

planner_observations_updated
planner_context_built

Example payloads:

{
"observation_count": 2
}

{
"observation_summaries": [...]
}

---

## 8. Example

Update examples/run_planner.py

Demonstrate:

### Deterministic mode

* planner reacts only to tool observations

### Cognitive mode

* planner reacts to observations
* planner selects explain_number capability dynamically

Demonstrate:

* no hardcoded iteration branching
* observation-driven next-step selection

Print:

* observation summaries
* planner context summaries

---

## 9. HARD RULES

DO NOT:

* create recursive self-reflection loops
* expose raw traces to planner
* dump entire memory into planner prompt
* hardcode planner iteration sequencing
* couple planner to execution engine internals

Planner MUST:

* remain bounded
* remain deterministic
* reason from observations

---

## 10. DESIGN INTENT

This step transitions Freya from:

* iterative orchestration

to:

* adaptive observation-aware planning

The planner should now synthesize next DAG fragments from execution state.

NOT from scripted iteration order.

---

# OUTPUT FORMAT

Provide:

1. New models/files
2. PlanningContext updates
3. Observation collection logic
4. Context builder implementation
5. Planner prompt rewrite
6. Updated examples
7. Trace integration

Do NOT explain.
Only output code.
