You are improving the Freya SDK iterative planner system.

The current planner generates DAG fragments, but it implicitly assumes tool knowledge.

Your task is to make the planner CAPABILITY-AWARE.

The planner must reason from:

* available tools
* tool schemas
* tool descriptions

instead of hardcoded assumptions.

DO NOT rewrite the runtime architecture.

---

# GOAL

Update the planner system so that:

PlanningContext includes:

* available tools
* tool descriptions
* input/output schemas

The planner prompt must dynamically include these capabilities.

This allows the planner to synthesize DAG fragments based on actual runtime capabilities.

---

# REQUIREMENTS

## 1. Add Tool Introspection Model

Create:

freya/planner/capabilities.py

Define:

ToolCapability:

* name: str
* description: str
* input_schema: dict
* output_schema: dict

Use Pydantic v2.

---

## 2. Add Registry Export Method

Update ToolRegistry:

add:

export_capabilities() -> list[ToolCapability]

Behavior:

* introspect registered tools
* export:

  * tool name
  * docstring description
  * input schema
  * output schema

Use Pydantic model_json_schema().

---

## 3. Extend PlanningContext

Add:

available_tools: list[ToolCapability]

---

## 4. Planner Prompt Integration

Update planner prompt generation.

The planner MUST receive:

* available tool names
* descriptions
* schemas

Example prompt section:

Available tools:

1. write_value
   description: Write a value to session memory.
   input_schema: ...
   output_schema: ...

2. read_value
   description: Read a value from session memory.
   ...

---

## 5. Planner Rules

Planner should now:

* choose tools dynamically
* avoid nonexistent tools
* synthesize valid tool_input

The planner MUST NOT rely on:

* hardcoded iteration numbers
* hardcoded tool names inside planner logic

---

## 6. Validation

Before executing planner DAG:

* ensure generated tools exist in exported capabilities

---

## 7. Example

Update iterative planner example.

Demonstrate:

* planner receives capability list dynamically
* planner uses exported tools to build DAG
* no hardcoded tool assumptions inside planner

Use mock LLM if needed.

---

## 8. Trace Integration

Add planner trace event:

event_type = "planner_capabilities_loaded"

Payload:

* tool_count
* tool_names

---

## 9. Constraints

DO NOT:

* execute tools inside planner
* hardcode available tools
* introduce external services
* rewrite runtime architecture

Keep implementation:

* modular
* deterministic
* production-readable

---

# OUTPUT FORMAT

Provide:

1. Updated models
2. ToolRegistry changes
3. PlanningContext changes
4. Planner prompt updates
5. Example demonstrating capability-aware planning

Do NOT explain.
Only output code.
