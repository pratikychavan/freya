You are working inside the Freya SDK repository.

Freya already supports:

* ExecutionEngine
* DAGRunner
* ToolRegistry
* PromptRegistry
* IterativePlannerRunner
* SimpleIterativePlanner
* PlanningContext
* Worker runtime
* Memory layer
* Trace system

The architecture is already stable and modular.

Your task is to implement:

1. PlanningMode abstraction
2. PromptCapabilityRegistry
3. Dual-mode planner support:

   * deterministic mode
   * cognitive mode

IMPORTANT:
Do NOT rewrite the runtime architecture.

The runtime must remain shared.
Only the planner capability surface changes by mode.

---

# ARCHITECTURE GOAL

Freya must support TWO planner modes:

## 1. Deterministic Mode

Planner sees:

* Tool capabilities only

Used for:

* deterministic workflows
* enterprise-safe orchestration
* low-cognition workflows

Planner may generate:

* tool tasks
* simple llm tasks

Planner MUST NOT:

* reason over prompt capabilities
* use semantic cognition patterns

---

## 2. Cognitive Mode

Planner sees:

* tool capabilities
* prompt capabilities
* semantic context
* memory summaries

Used for:

* adaptive planning
* reasoning workflows
* advanced agentic behavior

Planner MAY:

* select prompt capabilities dynamically
* orchestrate cognition patterns

---

# REQUIREMENTS

## 1. Add PlanningMode

Create:

freya/planner/mode.py

Define:

class PlanningMode(str, Enum):
DETERMINISTIC = "deterministic"
COGNITIVE = "cognitive"

---

## 2. Add PromptCapability model

Create:

freya/planner/prompt_capabilities.py

Define:

PromptCapability:

* name: str
* purpose: str
* description: str
* required_inputs: list[str]
* output_description: str
* planning_mode: PlanningMode

Use Pydantic v2.

---

## 3. Add PromptCapabilityRegistry

Create:

freya/prompts/capability_registry.py

Responsibilities:

* register PromptCapability
* retrieve capabilities
* filter by planning mode

Methods:

* register(capability)
* list_capabilities(mode=None)

Raise clear errors on duplicates.

---

## 4. Extend PlanningContext

Add:

planning_mode: PlanningMode
available_prompt_capabilities: list[PromptCapability]

---

## 5. Planner Behavior

Update SimpleIterativePlanner:

If mode == DETERMINISTIC:

* planner receives ONLY tool capabilities

If mode == COGNITIVE:

* planner receives:

  * tool capabilities
  * prompt capabilities
  * semantic context summary
  * memory summary

DO NOT expose cognitive prompt capabilities in deterministic mode.

---

## 6. Prompt Capability Prompting

Planner prompt must include section:

Available prompt capabilities:

* summarize_logs
  purpose: log_analysis
  required_inputs: ["log_text"]
  output: "summary of important failures"

* explain_number
  purpose: explanation
  required_inputs: ["value"]
  output: "human-readable explanation"

ONLY include this section in cognitive mode.

---

## 7. Trace Integration

Add trace events:

planner_mode_selected
planner_prompt_capabilities_loaded

Payload examples:

{
"mode": "cognitive"
}

{
"capability_names": [...]
}

---

## 8. Example Prompt Capabilities

Create at least:

1. explain_number
2. summarize_logs
3. classify_error

---

## 9. Example Usage

Update examples/run_planner.py

Demonstrate BOTH modes:

### Deterministic Mode

* planner only sees tools

### Cognitive Mode

* planner sees prompt capabilities
* planner uses explain_number capability

Print:

* planning mode
* loaded prompt capabilities

---

## 10. HARD RULES

DO NOT:

* merge ToolRegistry and PromptCapabilityRegistry
* expose prompt templates directly as planner capabilities
* allow planner to mutate memory directly
* couple planner logic to runtime execution
* rewrite DAGRunner or ExecutionEngine

Keep architecture:

* modular
* layered
* production-readable

---

# DESIGN INTENT

Tool capabilities represent:

* system actions

Prompt capabilities represent:

* reasoning operations

These MUST remain separate abstractions.

---

# OUTPUT FORMAT

Provide:

1. New folder/file structure
2. Full implementation
3. Updated planner integration
4. Updated examples
5. Trace integration

Do NOT explain.
Only output code.
