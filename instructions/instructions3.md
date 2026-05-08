You are building a production-grade Python SDK for an agent execution system.

You have already implemented:

* ExecutionEngine (runs tasks)
* DAGRunner (executes workflows)

Your task is to implement **Step 3: Tool System with Strict Schema Enforcement**.

---

## Goal

Build a robust tool system that:

* Enforces strict input/output contracts
* Prevents invalid tool execution
* Integrates cleanly with ExecutionEngine

---

## Requirements

### 1. Tool Base Class

Use Python + Pydantic.

Define abstract base class:

* name: str
* input_model: Pydantic model
* output_model: Pydantic model

Method:

* async execute(input: BaseModel) -> BaseModel

---

## 2. Tool Registry

Implement in-memory registry:

Class: ToolRegistry

Methods:

* register(tool: Tool)
* get(name: str) -> Tool
* list_tools() -> list[str]

---

## 3. Input Validation

Before executing a tool:

* Validate raw input dict → input_model
* Raise structured error if invalid

---

## 4. Output Validation

After execution:

* Validate result against output_model
* If invalid:

  * mark task as FAILED
  * include validation error

---

## 5. ExecutionEngine Integration

Update ExecutionEngine behavior for tool tasks:

IF task.type == "tool":

1. Fetch tool from registry
2. Validate input using tool.input_model
3. Call tool.execute()
4. Validate output using tool.output_model
5. Return structured result

---

## 6. Error Handling

Handle these cases explicitly:

* Tool not found
* Input validation error
* Execution error
* Output validation error

All must return:
TaskResult with:

* status = FAILED
* meaningful error message

---

## 7. Example Tool

Provide at least one real tool:

Example:
AddNumbersTool

Input:

* a: int
* b: int

Output:

* result: int

---

## 8. Example Usage

* Register tool
* Run:

  * valid tool task
  * invalid input task (should fail)
  * invalid output scenario (simulate failure)

---

## 9. Constraints

* Do NOT use jsonschema (use Pydantic only)
* Do NOT add versioning
* Do NOT add remote registry
* Keep registry in-memory

---

## Output Format

Provide:

1. Updated folder structure
2. Full Python code (modular)
3. Example usage demonstrating:

   * success
   * input validation failure
   * output validation failure

---

## Quality Bar

* Strict type enforcement
* Clean error messages
* No silent failures
* Minimal but extensible design

---

Do NOT explain. Just output code.
