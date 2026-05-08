"""
Step 7 — Control Plane Integration (Pull Model) with MockTransport.

Pushes 3 tasks into a MockTransport queue; a Worker pulls and executes them.

Tasks:
  t1 — add_numbers tool  (should succeed)
  t2 — store_value tool  (should succeed)
  t3 — missing_tool      (should fail gracefully)

Run (no API key needed):
    python examples/worker_example.py
"""

from __future__ import annotations

import asyncio
import json
import logging
from unittest.mock import AsyncMock

from freya.engine import ExecutionEngine
from freya.registry import ToolRegistry
from freya.tools import AddNumbersTool, StoreValueTool, GetValueTool
from freya.transport.mock import MockTransport
from freya.worker import Worker

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")


def make_engine(registry: ToolRegistry) -> ExecutionEngine:
    mock_llm = AsyncMock()
    return ExecutionEngine(llm_adapter=mock_llm, tool_registry=registry)


async def main() -> None:
    # --- Set up registry ---
    registry = ToolRegistry()
    registry.register(AddNumbersTool())
    registry.register(StoreValueTool())
    registry.register(GetValueTool())

    engine = make_engine(registry)

    # --- Set up mock transport and push tasks ---
    transport = MockTransport()
    session = "session-abc-123"

    transport.push_task({
        "task_id": "t1",
        "session_id": session,
        "type": "tool",
        "input": {"tool_name": "add_numbers", "tool_input": {"a": 10, "b": 20}},
    })
    transport.push_task({
        "task_id": "t2",
        "session_id": session,
        "type": "tool",
        "input": {"tool_name": "store_value", "tool_input": {"key": "answer", "value": 42}},
    })
    transport.push_task({
        "task_id": "t3",
        "session_id": session,
        "type": "tool",
        "input": {"tool_name": "missing_tool", "tool_input": {}},
    })

    # --- Run worker for exactly 3 poll cycles (one per task) ---
    # poll_interval=0 so it doesn't sleep between tasks in this demo
    worker = Worker(
        worker_id="worker-1",
        transport=transport,
        engine=engine,
        poll_interval=0,
    )
    # 3 tasks + 1 empty poll to confirm queue is drained
    await worker.run(max_iterations=4)

    # --- Print results ---
    print("\n" + "=" * 60)
    print("  Results collected by MockTransport")
    print("=" * 60)
    for task_id, result in transport.all_results().items():
        status = result["status"]
        output = result.get("output")
        error = (result.get("error") or "").splitlines()[0] if result.get("error") else None
        mem_events = []
        for tt in result.get("trace", {}).get("task_traces", {}).values():
            mem_events += [e for e in tt.get("events", []) if e["event_type"] == "memory_access"]

        print(f"\n  [{task_id}]  {status}")
        if output:
            print(f"    output        : {output}")
        if error:
            print(f"    error         : {error}")
        if mem_events:
            labels = [f"{e['payload']['action']}({e['payload']['key']})" for e in mem_events]
            print(f"    memory events : {labels}")


if __name__ == "__main__":
    asyncio.run(main())
