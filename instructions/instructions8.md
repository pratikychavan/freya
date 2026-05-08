You are building a production-grade Python SDK for an agent execution system.

You have already implemented:

* ExecutionEngine
* DAGRunner
* Tool system (Pydantic validation)
* Tracing system
* Policy system
* Memory layer (session-scoped KV)

Your task is to implement **Step 7: Control Plane Integration (Pull Model) with Pluggable Transport**.

---

## Goal

Enable the SDK to:

* Work in **standalone mode** (no backend)
* Work in **connected mode** (pull tasks from control plane)
* Use a **pluggable transport layer** (HTTP now, SSH/gRPC later)

---

## Requirements

### 1. Transport Interface (Pluggable)

Define a transport abstraction:

class ControlPlaneTransport:

Methods:

* async fetch_next_task(worker_id: str) -> dict | None
* async submit_result(task_id: str, result: dict) -> None
* async heartbeat(worker_id: str) -> None

---

### 2. HTTP Transport (V1 Implementation)

Implement:

class HttpTransport(ControlPlaneTransport)

Use:

* httpx (async)

Endpoints (mockable):

GET /tasks/next?worker_id=...
→ returns:
{
"task_id": str,
"session_id": str,
"type": "llm" | "tool",
"input": dict,
"depends_on": list[str] (optional)
}

POST /tasks/{task_id}/result
→ body:
{
"status": "SUCCESS" | "FAILED",
"output": dict,
"error": str | None,
"trace": dict
}

POST /workers/{worker_id}/heartbeat

---

### 3. Worker (Pull Loop)

Implement:

class Worker

Constructor:

* worker_id: str
* transport: ControlPlaneTransport
* execution_engine
* dag_runner (optional)

---

### Method:

async run()

Behavior:

Loop:

1. heartbeat

2. fetch_next_task()

3. if no task:

   * sleep (configurable)
   * continue

4. execute task:

   * create ExecutionContext (session_id, task_id, memory)
   * run via ExecutionEngine

5. submit result (including trace)

6. repeat

---

### 4. Standalone Mode

SDK must still support:

sdk.run(dag)

WITHOUT requiring transport.

---

### 5. Context Integration

* session_id comes from fetched task
* memory must be scoped per session_id
* reuse memory across tasks of same session

---

### 6. Error Handling

* If execution fails:

  * send FAILED result
* If transport fails:

  * retry (basic retry, max 3)
* Worker must NOT crash

---

### 7. Extensibility (IMPORTANT)

Design transport so future implementations can be added:

Examples:

* SSHTransport (paramiko)
* GRPCTransport

DO NOT implement them now.

---

### 8. Example

Provide:

* Mock transport (in-memory queue)
* Worker running against mock transport
* Push few tasks into mock queue
* Show worker pulling and executing them

---

### 9. Logging

* Log:

  * task fetch
  * task execution
  * result submission
  * heartbeat

---

## Constraints

* No real backend required (mock transport is enough)
* No message queue (no Kafka, no Redis)
* No authentication yet
* Keep simple but production-structured

---

## Output Format

Provide:

1. Updated folder structure
2. Full Python code
3. Example:

   * mock control plane
   * worker execution loop

---

## Quality Bar

* Clean transport abstraction
* No tight coupling to HTTP
* Worker loop is robust
* SDK still usable standalone

---

Do NOT explain. Just output code.
