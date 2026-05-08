"""
Step 3 — Tool System with Strict Schema Enforcement

Demonstrates three scenarios:
  1. Valid input  → SUCCESS
  2. Invalid input (wrong types) → FAILED (input validation)
  3. Bad output from a buggy tool → FAILED (output validation)

Run (no API key needed — pure tool tasks):
    python examples/tool_validation_example.py
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

from pydantic import BaseModel

from freya.engine import ExecutionEngine
from freya.models import Task
from freya.registry import ToolRegistry
from freya.tool import Tool
from freya.tools import AddNumbersTool


# ---------------------------------------------------------------------------
# Buggy tool that returns output violating its own output_model
# ---------------------------------------------------------------------------

class BuggyInput(BaseModel):
    value: int


class BuggyOutput(BaseModel):
    result: int  # must be int


class BuggyTool(Tool):
    """Returns a string instead of the declared int — output validation must catch this."""

    name = "buggy"
    input_model = BuggyInput
    output_model = BuggyOutput

    async def execute(self, input: BuggyInput, context) -> Any:  # type: ignore[override]
        # Intentionally returns wrong type to trigger output validation failure
        return {"result": "not_an_int"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_engine(registry: ToolRegistry) -> ExecutionEngine:
    # LLM adapter is not exercised in this example; use a mock
    mock_llm = AsyncMock()
    return ExecutionEngine(llm_adapter=mock_llm, tool_registry=registry)


async def run_task(engine: ExecutionEngine, task_id: str, tool_name: str, tool_input: dict) -> None:
    task = Task(
        task_id=task_id,
        type="tool",
        input={"tool_name": tool_name, "tool_input": tool_input},
    )
    result = await engine.execute_task(task)
    status_label = f"[{result.status}]"
    print(f"\n{'='*55}")
    print(f" {task_id}  {status_label}")
    print(f"{'='*55}")
    if result.output:
        print(f"  Output : {result.output}")
    if result.error:
        # Print only the first meaningful line to keep output readable
        first_line = result.error.splitlines()[0]
        print(f"  Error  : {first_line}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    registry = ToolRegistry()
    registry.register(AddNumbersTool())
    registry.register(BuggyTool())

    print(f"Registered tools: {registry.list_tools()}")

    engine = make_engine(registry)

    # 1. Valid input — should succeed
    await run_task(engine, "valid-task", "add_numbers", {"a": 10, "b": 32})

    # 2. Invalid input — 'a' is a string, not int
    await run_task(engine, "bad-input-task", "add_numbers", {"a": "ten", "b": 5})

    # 3. Output validation failure — buggy tool returns wrong type
    await run_task(engine, "bad-output-task", "buggy", {"value": 99})


if __name__ == "__main__":
    asyncio.run(main())
