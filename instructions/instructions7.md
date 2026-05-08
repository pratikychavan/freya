You are building a production-grade Python SDK for an agent execution system.

You have already implemented:

* ExecutionEngine
* DAGRunner
* Tool system with schema validation
* Tracing system
* Policy system

Your task is to implement **Step 6: Memory Layer (simple key-value, session-scoped)**.

---

## Goal

Build a minimal memory system that:

* Stores and retrieves data during execution
* Is scoped per session
* Is safe to use across DAG tasks
* Integrates with ExecutionEngine and DAGRunner

---

## Requirements

### 1. Memory Interface

Define base interface:

MemoryStore:

Methods:

* get(session_id: str, key: str) -> Any | None
* set(session_id: str, key: str, value: Any) -> None
* delete(session_id: str, key: str) -> None
* list_keys(session_id: str) -> list[str]

---

## 2. In-Memory Implementation

Class: InMemoryStore

* Use dict internally:
  {
  session_id: {
  key: value
  }
  }

---

## 3. Execution Context

Extend your existing context object:

ExecutionContext:

* session_id: str
* task_id: str
* memory: MemoryStore

---

## 4. ExecutionEngine Integration

Update task execution:

* Pass context to:

  * LLM execution (optional use)
  * Tool execution (required)

Tools must receive context:

async execute(input: BaseModel, context: ExecutionContext)

---

## 5. Tool Usage of Memory

Allow tools to:

* read from memory:
  context.memory.get(session_id, key)

* write to memory:
  context.memory.set(session_id, key, value)

---

## 6. DAGRunner Integration

* Initialize ONE shared MemoryStore per DAG run
* Ensure all tasks share the same session_id
* Pass same memory instance to all tasks

---

## 7. Safety Rules

* Memory MUST be isolated by session_id
* No cross-session leakage
* Missing keys should return None (not error)

---

## 8. Example Tools

Provide TWO tools:

---

### (A) StoreValueTool

Input:

* key: str
* value: Any

Behavior:

* stores value in memory

Output:

* {"status": "stored"}

---

### (B) GetValueTool

Input:

* key: str

Behavior:

* retrieves value from memory

Output:

* {"value": Any | None}

---

## 9. Example DAG

Create DAG:

Task A:

* StoreValueTool → store ("x", 42)

Task B:

* GetValueTool → depends_on A
* should return 42

---

## 10. Trace Integration

* Log memory operations:
  event_type: "memory_access"

Payload:

* action: "get" | "set"
* key
* value (optional for debug)

---

## Constraints

* No persistence (in-memory only)
* No Redis / DB
* No vector search
* No abstraction layers beyond this

---

## Output Format

Provide:

1. Updated folder structure
2. Full Python code
3. Example usage:

   * run DAG
   * show memory working
   * show trace including memory events

---

## Quality Bar

* Clean separation of memory layer
* No global state hacks
* Safe session isolation
* Simple, readable implementation

---

Do NOT explain. Just output code.
