# Freya SDK

Production-grade Python SDK for building agent execution systems. Provides a composable set of layers — task execution, tool dispatch, memory, policy, tracing, DAG orchestration, and pull-based workers — that can be used independently or together.

- **Python ≥ 3.11**, fully async (`asyncio`)
- **Pydantic v2** for all data models and tool contracts
- No runtime dependencies beyond `pydantic`, `openai`, and `httpx`

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Architecture Overview](#architecture-overview)
4. [Core Concepts](#core-concepts)
   - [Task & TaskResult](#task--taskresult)
   - [LLMAdapter](#llmadapter)
   - [Tool System](#tool-system)
   - [ExecutionEngine](#executionengine)
   - [Memory](#memory)
   - [Policy](#policy)
   - [Tracing](#tracing)
   - [DAG Execution](#dag-execution)
   - [Worker](#worker)
   - [Transport](#transport)
5. [API Reference](#api-reference)
6. [Examples](#examples)

---

## Installation

```bash
pip install -e .
```

Install with dev dependencies:

```bash
pip install -e ".[dev]"
```

---

## Quick Start

### Run a single tool task

```python
import asyncio
from unittest.mock import AsyncMock
from freya import ExecutionEngine, ToolRegistry, Task
from freya.tools import AddNumbersTool

async def main():
    registry = ToolRegistry()
    registry.register(AddNumbersTool())

    engine = ExecutionEngine(llm_adapter=AsyncMock(), tool_registry=registry)

    task = Task(
        task_id="t1",
        type="tool",
        input={"tool_name": "add_numbers", "tool_input": {"a": 3, "b": 4}},
    )
    result = await engine.execute_task(task)
    print(result.status, result.output)   # SUCCESS {'result': 7}

asyncio.run(main())
```

### Run a DAG

```python
from freya import DAG, DAGTask, DAGRunner, ExecutionEngine, ToolRegistry
from freya.tools import AddNumbersTool

async def main():
    registry = ToolRegistry()
    registry.register(AddNumbersTool())
    engine = ExecutionEngine(llm_adapter=AsyncMock(), tool_registry=registry)
    runner = DAGRunner(engine)

    dag = DAG(tasks=[
        DAGTask(task_id="a", type="tool",
                input={"tool_name": "add_numbers", "tool_input": {"a": 1, "b": 2}}),
        DAGTask(task_id="b", type="tool", depends_on=["a"],
                input={"tool_name": "add_numbers", "tool_input": {"a": 0, "b": 10}}),
    ])
    result = await runner.run(dag)
    print(result.status)   # SUCCESS
```

### Pull-based worker

```python
from freya import Worker, ExecutionEngine, ToolRegistry
from freya.transport import MockTransport
from freya.tools import AddNumbersTool

async def main():
    registry = ToolRegistry()
    registry.register(AddNumbersTool())
    engine = ExecutionEngine(llm_adapter=AsyncMock(), tool_registry=registry)

    transport = MockTransport()
    transport.push_task({
        "task_id": "t1",
        "session_id": "s1",
        "type": "tool",
        "input": {"tool_name": "add_numbers", "tool_input": {"a": 5, "b": 5}},
        "is_terminal": True,
    })

    worker = Worker(worker_id="w1", transport=transport, engine=engine)
    await worker.run(max_iterations=5)

    print(transport.get_result("t1"))  # {'status': 'SUCCESS', 'output': {'result': 10}, ...}
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                        Worker                           │
│  (pull loop, session lock, idempotency, TTL cleanup)    │
└────────────────────┬────────────────────────────────────┘
                     │ execute_task()
┌────────────────────▼────────────────────────────────────┐
│                  ExecutionEngine                        │
│  Policy pre-check → execute (LLM / Tool) → Policy post │
└───┬──────────────┬──────────────┬───────────────────────┘
    │              │              │
┌───▼───┐  ┌──────▼──────┐  ┌───▼────────┐
│ LLM   │  │ ToolRegistry │  │  Memory    │
│Adapter│  │  + Tools     │  │  Store     │
└───────┘  └─────────────┘  └────────────┘

┌─────────────────────────────────────────────────────────┐
│                      DAGRunner                         │
│  Topological sort → parallel generations → Engine      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│             Tracing  /  Policy  /  Transport            │
└─────────────────────────────────────────────────────────┘
```

Every layer is independently usable. You can run the engine directly without a worker, use the DAGRunner without policies, or use the memory store in your own tools.

---

## Core Concepts

### Task & TaskResult

A `Task` is the unit of work passed to `ExecutionEngine`.

```python
from freya import Task

task = Task(
    task_id="unique-id",           # required
    type="tool",                   # "tool" | "llm"
    input={...},                   # task-specific payload
    config={},                     # optional config dict
)
```

**Tool task input format:**
```python
{"tool_name": "my_tool", "tool_input": {"field": "value"}}
```

**LLM task input format:**
```python
{"prompt": "Summarise this text...", "model": "gpt-4o-mini"}  # model optional
```

A `TaskResult` is the outcome:

```python
result.status       # "SUCCESS" | "FAILED"
result.output       # dict | None
result.error        # str | None  — full error message + traceback
result.error_type   # "TOOL_NOT_FOUND" | "VALIDATION_ERROR" | "POLICY_BLOCK" | "EXECUTION_ERROR" | None
result.duration_ms  # int
result.trace        # Trace | None  — legacy trace object
```

---

### LLMAdapter

`LLMAdapter` is a `Protocol`. Implement it to connect any LLM provider.

```python
from freya import LLMAdapter
from typing import AsyncIterator, Any

class MyAdapter:
    async def complete(self, request: dict[str, Any]) -> dict[str, Any]: ...
    async def stream(self, request: dict[str, Any]) -> AsyncIterator[str]: ...
    def supports_vision(self) -> bool: return False
    def supports_tool_calls(self) -> bool: return False
    def token_budget(self) -> int: return 8192
```

**Built-in: `OpenAIAdapter`**

```python
from freya.adapters import OpenAIAdapter

adapter = OpenAIAdapter(api_key="sk-...", default_model="gpt-4o-mini")
# or reads OPENAI_API_KEY from environment
adapter = OpenAIAdapter()
```

The adapter expects `request["prompt"]` (string) and optionally `request["model"]`. It returns:
```python
{"text": "...", "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}
```

---

### Tool System

Define a tool by subclassing `Tool` with three class variables:

```python
from pydantic import BaseModel
from freya import Tool, ExecutionContext

class MultiplyInput(BaseModel):
    a: float
    b: float

class MultiplyOutput(BaseModel):
    result: float

class MultiplyTool(Tool):
    name = "multiply"
    input_model = MultiplyInput
    output_model = MultiplyOutput

    async def execute(self, input: MultiplyInput, context: ExecutionContext) -> MultiplyOutput:
        return MultiplyOutput(result=input.a * input.b)
```

The engine validates input against `input_model` before calling `execute`, and validates the return value against `output_model` after. Validation failures produce `VALIDATION_ERROR` task results.

**Register and use tools:**

```python
from freya import ToolRegistry

registry = ToolRegistry()
registry.register(MultiplyTool())

registry.list_tools()    # ["multiply"]
registry.get("multiply") # MultiplyTool instance
```

**Built-in tools:**

| Name | Class | Description |
|------|-------|-------------|
| `add_numbers` | `AddNumbersTool` | Returns `a + b` |
| `store_value` | `StoreValueTool` | Saves a key-value pair to session memory |
| `get_value` | `GetValueTool` | Retrieves a value from session memory |

```python
from freya.tools import AddNumbersTool, StoreValueTool, GetValueTool
```

---

### ExecutionEngine

Central executor. Takes an `LLMAdapter`, `ToolRegistry`, and optional `PolicyManager`.

```python
from freya import ExecutionEngine

engine = ExecutionEngine(
    llm_adapter=adapter,
    tool_registry=registry,
    policy_manager=pm,     # optional
)

result = await engine.execute_task(
    task,
    trace_manager=tm,      # optional — attach a TraceManager for structured tracing
    memory=store,          # optional — pass a shared MemoryStore (required for cross-task memory)
    session_id="sess-1",   # optional — pass the real session id (required when memory is shared)
)
```

> **Important**: When running tasks in a Worker or multi-task scenario, always pass both `memory` and `session_id` explicitly so that memory data is scoped to the correct session.

**Execution flow:**

1. Policy input check (if `PolicyManager` attached)
2. Execute task (`_execute_llm` or `_execute_tool`)
3. Policy output check (if `PolicyManager` attached)
4. Return `TaskResult`

If any policy returns `BLOCK`, execution stops immediately with `error_type="POLICY_BLOCK"`.

---

### Memory

`MemoryStore` is a session-scoped key-value store interface.

```python
from freya import MemoryStore, InMemoryStore

store = InMemoryStore()

store.set("sess-1", "user_name", "Alice")
store.get("sess-1", "user_name")       # "Alice"
store.list_keys("sess-1")              # ["user_name"]
store.delete("sess-1", "user_name")
store.cleanup_session("sess-1")        # removes all keys for the session
```

**In tools**, access memory via `ExecutionContext`:

```python
async def execute(self, input: MyInput, context: ExecutionContext) -> MyOutput:
    prev = context.memory.get(context.session_id, "my_key")
    context.memory.set(context.session_id, "my_key", input.value)
    return MyOutput(...)
```

**Custom store**: implement `MemoryStore` to plug in Redis, DynamoDB, etc.:

```python
class RedisStore(MemoryStore):
    def get(self, session_id, key): ...
    def set(self, session_id, key, value): ...
    def delete(self, session_id, key): ...
    def list_keys(self, session_id): ...
    def cleanup_session(self, session_id): ...
```

> **Note**: `InMemoryStore` holds data in-process RAM only. It is not thread-safe and not suitable for multi-process deployments without replacement.

---

### Policy

Policies run before and after every task execution. They return `ALLOW`, `WARN`, or `BLOCK`.

```python
from freya import Policy, PolicyResult
from typing import Any

class WordCountPolicy(Policy):
    def check_input(self, task: dict, context: dict) -> PolicyResult:
        prompt = task.get("input", {}).get("prompt", "")
        if len(prompt.split()) > 500:
            return PolicyResult(action="BLOCK", reason="Prompt too long")
        return PolicyResult(action="ALLOW")

    def check_output(self, task: dict, result: dict, context: dict) -> PolicyResult:
        return PolicyResult(action="ALLOW")
```

**PolicyManager** applies policies in registration order and short-circuits on the first `BLOCK`:

```python
from freya import PolicyManager

pm = PolicyManager()
pm.add_policy(WordCountPolicy())
pm.add_policy(AnotherPolicy())

engine = ExecutionEngine(llm_adapter=..., tool_registry=..., policy_manager=pm)
```

**Built-in policies:**

| Class | Applies to | Behaviour |
|-------|-----------|-----------|
| `MaxLengthPolicy(max_chars=1000)` | LLM tasks | BLOCKs if `input.prompt` exceeds `max_chars` |
| `RequiredFieldPolicy(required_fields=[...])` | Tool tasks | BLOCKs if any field missing from `tool_input` |
| `PromptKeywordPolicy(keywords=[...])` | LLM tasks | WARNs (allows execution) if any keyword found in prompt |

```python
from freya import MaxLengthPolicy, RequiredFieldPolicy, PromptKeywordPolicy
```

---

### Tracing

Tracing records structured events for every task execution.

```python
from freya import TraceManager

tm = TraceManager()
result = await engine.execute_task(task, trace_manager=tm)
tm.finalize(result.status)

trace = tm.export_dag_trace()
# {
#   "session_id": "...",
#   "task_traces": {
#     "t1": {
#       "task_id": "t1",
#       "start_time": 1234567890.123,
#       "end_time": 1234567890.456,
#       "status": "SUCCESS",
#       "events": [
#         {"event_type": "task_started", ...},
#         {"event_type": "tool_call_started", "payload": {"tool_name": "..."}, ...},
#         {"event_type": "tool_call_completed", ...},
#         {"event_type": "task_completed", ...}
#       ]
#     }
#   }
# }
```

**Event types emitted automatically:**

| Event | When |
|-------|------|
| `task_started` | Task begins |
| `task_completed` | Task succeeds |
| `task_failed` | Task fails |
| `llm_call_started` / `llm_call_completed` | Around LLM call |
| `tool_call_started` / `tool_call_completed` | Around tool call |
| `policy_check` | Each policy evaluated (payload includes `stage`, `policy_name`, `action`, `reason`) |
| `memory_access` | Each memory read/write (payload includes `action`, `key`, `value`, `truncated`) |

---

### DAG Execution

`DAGRunner` executes a directed acyclic graph of tasks. Tasks with no shared dependencies run in parallel.

```python
from freya import DAG, DAGTask, DAGRunner

dag = DAG(tasks=[
    DAGTask(task_id="fetch",
            type="tool",
            input={"tool_name": "...", "tool_input": {...}}),

    DAGTask(task_id="process",
            type="tool",
            depends_on=["fetch"],      # runs after "fetch"
            input={"tool_name": "...", "tool_input": {...}}),

    DAGTask(task_id="notify",
            type="tool",
            depends_on=["fetch"],      # also runs after "fetch", in parallel with "process"
            input={"tool_name": "...", "tool_input": {...}}),
])

runner = DAGRunner(engine)
dag_result = await runner.run(dag)

dag_result.status          # "SUCCESS" | "FAILED"
dag_result.results["process"].output   # output dict for the "process" task
dag_result.dag_trace       # DAGTrace with all task events
```

**Dependency output injection**: when a task depends on others, the outputs of those tasks are merged into the dependent task's input under the parent's `task_id` as a key:

```python
# "process" receives:
# input = {
#     "tool_name": "...",
#     "tool_input": {...},
#     "fetch": {"result": ...}    ← injected automatically
# }
```

If a dependency fails, all tasks that depend on it (transitively) are skipped. The DAG result `status` is `"FAILED"` if any task failed or was skipped.

**Validation** (runs before execution):
```python
from freya import DAGValidationError

try:
    runner.run(dag)
except DAGValidationError as e:
    print(e)   # "Cycle detected" | "Unknown dependency: ..."
```

---

### Worker

`Worker` implements a pull-based execution loop. It fetches tasks from a control plane, executes them, and submits results back.

```python
from freya import Worker

worker = Worker(
    worker_id="worker-1",
    transport=transport,     # ControlPlaneTransport
    engine=engine,
    poll_interval=1.0,       # seconds to sleep when queue is empty (before backoff kicks in)
)

await worker.run()               # runs forever
await worker.run(max_iterations=100)  # runs for 100 poll cycles
worker.stop()                    # graceful stop from another coroutine
```

**Task dict format** (fetched from transport):

```python
{
    "task_id": "t1",           # required, unique
    "session_id": "s1",        # required, determines memory scope
    "type": "tool",            # "tool" | "llm"
    "input": {...},            # task input
    "config": {},              # optional
    "is_terminal": True,       # optional — triggers immediate memory cleanup
}
```

**Built-in features:**

| Feature | Behaviour |
|---------|-----------|
| Exponential backoff | Idle sleep doubles each empty poll: 0.1s → 0.2s → ... → 5.0s cap |
| Session lock | At most one task per session executes concurrently on the same worker |
| Idempotency cache | Duplicate `task_id` is resubmitted from cache without re-executing |
| TTL cleanup | Sessions idle for ≥ 60 seconds have their memory wiped (configurable via `_SESSION_TTL_SECONDS`) |
| Terminal cleanup | `is_terminal: true` in task dict triggers immediate `cleanup_session()` |
| Submit retries | Failed result submissions retry up to 3 times with 0.5s × attempt backoff |
| Heartbeat | Sent to transport before each poll cycle; failures are logged but non-fatal |

> **Note**: The idempotency cache (`_executed_tasks`) is in-process only. For multi-worker idempotency guarantees, the control plane must own task-status persistence.

---

### Transport

`ControlPlaneTransport` is the interface between a Worker and its control plane.

```python
from freya import ControlPlaneTransport

class ControlPlaneTransport(ABC):
    async def fetch_next_task(self, worker_id: str) -> dict | None: ...
    async def submit_result(self, task_id: str, result: dict) -> None: ...
    async def heartbeat(self, worker_id: str) -> None: ...
```

**`HttpTransport`** — connects to a REST control plane:

```python
from freya import HttpTransport

transport = HttpTransport(base_url="https://my-control-plane.example.com", timeout=10.0)
```

| Method | Endpoint |
|--------|----------|
| `fetch_next_task` | `GET /tasks/next?worker_id={id}` → 200 (task) or 204 (empty) |
| `submit_result` | `POST /tasks/{task_id}/result` with JSON body |
| `heartbeat` | `POST /workers/{worker_id}/heartbeat` |

**`MockTransport`** — in-memory, for testing and examples:

```python
from freya import MockTransport

transport = MockTransport()
transport.push_task({...})                  # enqueue a task
transport.get_result("task-id")             # retrieve single result
transport.all_results()                     # retrieve all results as dict
```

---

## API Reference

### `freya` (top-level exports)

| Name | Type | Module |
|------|------|--------|
| `Task` | Pydantic model | `freya.models` |
| `TaskResult` | Pydantic model | `freya.models` |
| `Trace` | Pydantic model | `freya.trace` |
| `LLMAdapter` | Protocol | `freya.adapter` |
| `Tool` | Abstract base class | `freya.tool` |
| `ToolRegistry` | Class | `freya.registry` |
| `ExecutionEngine` | Class | `freya.engine` |
| `ExecutionContext` | Dataclass | `freya.context` |
| `MemoryStore` | Abstract base class | `freya.memory.store` |
| `InMemoryStore` | Class | `freya.memory.store` |
| `DAG` | Pydantic model | `freya.dag.models` |
| `DAGTask` | Pydantic model | `freya.dag.models` |
| `DAGResult` | Pydantic model | `freya.dag.models` |
| `DAGRunner` | Class | `freya.dag.runner` |
| `DAGValidationError` | Exception | `freya.dag.validation` |
| `TraceEvent` | Pydantic model | `freya.tracing.models` |
| `TaskTrace` | Pydantic model | `freya.tracing.models` |
| `DAGTrace` | Pydantic model | `freya.tracing.models` |
| `TraceManager` | Class | `freya.tracing.manager` |
| `Policy` | Abstract base class | `freya.policy.base` |
| `PolicyResult` | Pydantic model | `freya.policy.base` |
| `PolicyManager` | Class | `freya.policy.manager` |
| `MaxLengthPolicy` | Class | `freya.policy.policies` |
| `RequiredFieldPolicy` | Class | `freya.policy.policies` |
| `PromptKeywordPolicy` | Class | `freya.policy.policies` |
| `ControlPlaneTransport` | Abstract base class | `freya.transport.base` |
| `HttpTransport` | Class | `freya.transport.http` |
| `MockTransport` | Class | `freya.transport.mock` |
| `Worker` | Class | `freya.worker` |

### `freya.adapters`

| Name | Type |
|------|------|
| `OpenAIAdapter` | Class |

### `freya.tools`

| Name | Type |
|------|------|
| `AddNumbersTool` | Class |
| `StoreValueTool` | Class |
| `GetValueTool` | Class |

---

## Examples

All runnable examples are in [`examples/`](../examples/). None require an OpenAI API key (they use `AsyncMock`).

| File | What it shows |
|------|---------------|
| [example.py](../examples/example.py) | Basic single-task engine usage (LLM + tool) |
| [tool_validation_example.py](../examples/tool_validation_example.py) | Input/output validation pass and failure |
| [policy_example.py](../examples/policy_example.py) | BLOCK, WARN, and ALLOW policy actions |
| [memory_example.py](../examples/memory_example.py) | Cross-task memory read/write via `StoreValueTool` / `GetValueTool` |
| [tracing_example.py](../examples/tracing_example.py) | Full `DAGTrace` export with event log |
| [dag_example.py](../examples/dag_example.py) | Parallel task generations and dependency injection |
| [worker_example.py](../examples/worker_example.py) | Worker pull loop with `MockTransport` |
| [hardening_example.py](../examples/hardening_example.py) | `error_type` classification, idempotency, value truncation in traces |
| [lifecycle_example.py](../examples/lifecycle_example.py) | Session lifecycle: terminal flag cleanup, memory persistence across tasks |

Run any example:
```bash
python examples/lifecycle_example.py
```
