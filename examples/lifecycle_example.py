"""
Step 11 — Session Lifecycle / Safe Memory Cleanup example.

Demonstrates:
  - Two tasks in the same session: memory persists correctly between them
  - Terminal flag (is_terminal=True) triggers immediate cleanup after last task
  - Without terminal flag, memory is NOT prematurely cleaned between tasks
  - TTL-based cleanup is also available (sweep runs every task cycle)
  - memory_cleanup log shows reason="terminal" or reason="ttl"

Run:
    python examples/lifecycle_example.py
"""

from __future__ import annotations

import asyncio
import logging

from freya.engine import ExecutionEngine
from freya.registry import ToolRegistry
from freya.tools import AddNumbersTool, StoreValueTool, GetValueTool
from freya.transport.mock import MockTransport
from freya.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s  %(message)s",
)


async def main() -> None:
    registry = ToolRegistry()
    registry.register(AddNumbersTool())
    registry.register(StoreValueTool())
    registry.register(GetValueTool())

    from unittest.mock import AsyncMock
    engine = ExecutionEngine(llm_adapter=AsyncMock(), tool_registry=registry)
    transport = MockTransport()

    # Session "sess-A": two tasks.
    # task-A1 stores a value; task-A2 reads it back.
    # Memory must persist between the two tasks — no premature cleanup.
    transport.push_task({
        "task_id": "task-A1",
        "session_id": "sess-A",
        "type": "tool",
        "input": {"tool_name": "store_value", "tool_input": {"key": "greeting", "value": "hello"}},
    })
    transport.push_task({
        "task_id": "task-A2",
        "session_id": "sess-A",
        "type": "tool",
        "input": {"tool_name": "get_value", "tool_input": {"key": "greeting"}},
        # is_terminal marks this as the last task for the session — triggers immediate cleanup.
        "is_terminal": True,
    })

    # Session "sess-B": independent, also uses terminal flag.
    transport.push_task({
        "task_id": "task-B1",
        "session_id": "sess-B",
        "type": "tool",
        "input": {"tool_name": "add_numbers", "tool_input": {"a": 10, "b": 20}},
        "is_terminal": True,
    })

    worker = Worker(
        worker_id="w1",
        transport=transport,
        engine=engine,
        poll_interval=0,
    )
    await worker.run(max_iterations=10)

    results = transport.all_results()

    print("\n" + "=" * 60)
    print("  Session Lifecycle Results")
    print("=" * 60)

    for task_id in ("task-A1", "task-A2", "task-B1"):
        r = results.get(task_id, {})
        print(f"\n[{task_id}]  status={r.get('status')}  output={r.get('output')}")

    print("\n--- Memory state after all tasks ---")
    for sid in ("sess-A", "sess-B"):
        remaining = worker._memory.list_keys(sid)
        cleaned = remaining == []
        print(f"[{sid}]  remaining_keys={remaining}  cleaned={cleaned}")


if __name__ == "__main__":
    asyncio.run(main())
