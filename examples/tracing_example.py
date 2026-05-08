"""
Step 4 — Tracing System example.

DAG:
  task-ok   (tool) — succeeds
  task-fail (tool) — fails (tool not registered → FAILED)

Prints the full exported DAGTrace.

Run (no API key needed):
    python examples/tracing_example.py
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

from pydantic import BaseModel

from freya.dag import DAG, DAGRunner, DAGTask
from freya.engine import ExecutionEngine
from freya.registry import ToolRegistry
from freya.tool import Tool
from freya.tools import AddNumbersTool


def make_engine(registry: ToolRegistry) -> ExecutionEngine:
    mock_llm = AsyncMock()
    return ExecutionEngine(llm_adapter=mock_llm, tool_registry=registry)


async def main() -> None:
    registry = ToolRegistry()
    registry.register(AddNumbersTool())
    # intentionally NOT registering "missing_tool" to trigger failure

    engine = make_engine(registry)
    runner = DAGRunner(engine=engine)

    dag = DAG(
        tasks=[
            # succeeds
            DAGTask(
                task_id="task-ok",
                type="tool",
                input={"tool_name": "add_numbers", "tool_input": {"a": 5, "b": 7}},
            ),
            # fails — tool not found
            DAGTask(
                task_id="task-fail",
                type="tool",
                input={"tool_name": "missing_tool", "tool_input": {}},
            ),
        ]
    )

    result = await runner.run(dag)

    print(f"DAG status : {result.status}\n")
    for task_id, tr in result.results.items():
        print(f"  [{task_id}] {tr.status}")

    print("\n--- Exported DAGTrace (JSON) ---\n")
    trace_dict = result.dag_trace.model_dump() if result.dag_trace else {}

    # Pretty-print; omit bulky fields for readability
    for task_id, tt in trace_dict.get("task_traces", {}).items():
        print(f"Task: {task_id}")
        print(f"  status      : {tt['status']}")
        print(f"  duration_ms : {round((tt['end_time'] - tt['start_time']) * 1000, 2)}")
        if tt["error"]:
            print(f"  error       : {tt['error'].splitlines()[0]}")
        print(f"  events:")
        for ev in tt["events"]:
            print(f"    [{ev['event_type']}]  payload={ev['payload']}")
        print()

    print(f"DAGTrace session_id : {trace_dict.get('session_id')}")
    print(f"DAGTrace status     : {trace_dict.get('status')}")


if __name__ == "__main__":
    asyncio.run(main())
