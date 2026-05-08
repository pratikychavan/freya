"""
Step 6 — Memory Layer example.

DAG:
  Task A  (StoreValueTool) — stores key "x" = 42
  Task B  (GetValueTool, depends on A) — reads key "x", should return 42

Shows:
  - shared session memory across tasks
  - memory_access trace events

Run (no API key needed):
    python examples/memory_example.py
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock

from freya.dag import DAG, DAGRunner, DAGTask
from freya.engine import ExecutionEngine
from freya.registry import ToolRegistry
from freya.tools import AddNumbersTool, GetValueTool, StoreValueTool

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")


def make_engine(registry: ToolRegistry) -> ExecutionEngine:
    mock_llm = AsyncMock()
    return ExecutionEngine(llm_adapter=mock_llm, tool_registry=registry)


async def main() -> None:
    registry = ToolRegistry()
    registry.register(StoreValueTool())
    registry.register(GetValueTool())
    registry.register(AddNumbersTool())

    engine = make_engine(registry)
    runner = DAGRunner(engine=engine)

    dag = DAG(
        tasks=[
            # Task A — stores x=42
            DAGTask(
                task_id="task-store",
                type="tool",
                input={"tool_name": "store_value", "tool_input": {"key": "x", "value": 42}},
            ),
            # Task B — reads x (depends on A so it runs after store)
            DAGTask(
                task_id="task-get",
                type="tool",
                input={"tool_name": "get_value", "tool_input": {"key": "x"}},
                depends_on=["task-store"],
            ),
        ]
    )

    result = await runner.run(dag)

    print(f"\nDAG status: {result.status}\n")
    for task_id, tr in result.results.items():
        print(f"  [{task_id}]  {tr.status}  →  {tr.output}")

    # Show memory_access trace events
    if result.dag_trace:
        print("\n--- Memory Events in Trace ---")
        for task_id, tt in result.dag_trace.task_traces.items():
            mem_events = [e for e in tt.events if e.event_type == "memory_access"]
            if mem_events:
                print(f"\n  {task_id}:")
                for ev in mem_events:
                    p = ev.payload
                    print(f"    [{p['action']}]  key={p['key']}  value={p.get('value')}")


if __name__ == "__main__":
    asyncio.run(main())
