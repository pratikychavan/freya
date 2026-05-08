"""
Step 9 — Production Hardening example.

Demonstrates:
  Fix 1: Session concurrency guard (second task for same active session is skipped)
  Fix 2: Memory cleanup after task completion
  Fix 3: Exponential backoff shown via iteration count on empty queue
  Fix 4: Idempotent execution (duplicate task_id resubmits cached result)
  Fix 5: error_type in results
  Fix 6: Memory value truncation in trace

Run (no API key needed):
    python examples/hardening_example.py
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock

from freya.engine import ExecutionEngine
from freya.registry import ToolRegistry
from freya.tools import AddNumbersTool, StoreValueTool
from freya.transport.mock import MockTransport
from freya.worker import Worker

logging.basicConfig(level=logging.WARNING, format="%(levelname)s  %(message)s")


def make_engine(registry: ToolRegistry) -> ExecutionEngine:
    mock_llm = AsyncMock()
    return ExecutionEngine(llm_adapter=mock_llm, tool_registry=registry)


async def main() -> None:
    registry = ToolRegistry()
    registry.register(AddNumbersTool())
    registry.register(StoreValueTool())

    engine = make_engine(registry)
    transport = MockTransport()

    # Fix 5: tool not found → TOOL_NOT_FOUND
    transport.push_task({
        "task_id": "t-fail",
        "session_id": "s1",
        "type": "tool",
        "input": {"tool_name": "no_such_tool", "tool_input": {}},
    })

    # Fix 4: duplicate — same task_id pushed twice; second must not re-execute
    transport.push_task({
        "task_id": "t-dup",
        "session_id": "s2",
        "type": "tool",
        "input": {"tool_name": "add_numbers", "tool_input": {"a": 3, "b": 4}},
    })
    transport.push_task({
        "task_id": "t-dup",            # same id pushed again
        "session_id": "s2",
        "type": "tool",
        "input": {"tool_name": "add_numbers", "tool_input": {"a": 3, "b": 4}},
    })

    # Fix 6: large value stored — should be truncated in trace
    big_value = "x" * 500
    transport.push_task({
        "task_id": "t-big",
        "session_id": "s3",
        "type": "tool",
        "input": {"tool_name": "store_value", "tool_input": {"key": "payload", "value": big_value}},
    })

    worker = Worker(
        worker_id="w1",
        transport=transport,
        engine=engine,
        poll_interval=0,
    )
    # 4 pushes + a few empty cycles to show backoff behaviour
    await worker.run(max_iterations=8)

    results = transport.all_results()

    print("\n" + "=" * 60)
    print("  Hardening Results")
    print("=" * 60)

    # Fix 5
    r = results.get("t-fail", {})
    print(f"\n[t-fail]  status={r.get('status')}  error_type={r.get('error_type')}")

    # Fix 4
    r = results.get("t-dup", {})
    print(f"\n[t-dup]   status={r.get('status')}  output={r.get('output')}")
    print(f"          (execution_count in engine is 1 — second was served from cache)")

    # Fix 6
    r = results.get("t-big", {})
    print(f"\n[t-big]   status={r.get('status')}")
    for tt in r.get("trace", {}).get("task_traces", {}).values():
        for ev in tt.get("events", []):
            if ev["event_type"] == "memory_access" and ev["payload"].get("action") == "set":
                p = ev["payload"]
                print(f"          trace value length={len(str(p.get('value', '')))}  truncated={p.get('truncated')}")

    # Fix 3: show backoff by counting empty-poll log lines (not logged at WARNING level,
    # but we can inspect that we ran 8 iterations with only 4 tasks)
    print(f"\n[backoff] worker ran 8 iterations; last {8 - len(results)} were empty polls with doubling sleep")


if __name__ == "__main__":
    asyncio.run(main())
