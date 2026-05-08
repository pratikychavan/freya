from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel

from freya import ExecutionEngine, Task, ToolRegistry
from freya.adapters.openai import OpenAIAdapter
from freya.tool import Tool


# ---------------------------------------------------------------------------
# Sample tool: adds two numbers
# ---------------------------------------------------------------------------

class AddInput(BaseModel):
    a: float
    b: float


class AddOutput(BaseModel):
    result: float


class AddTool(Tool):
    name = "add"
    input_model = AddInput
    output_model = AddOutput

    async def execute(self, input: AddInput, context) -> AddOutput:  # type: ignore[override]
        return AddOutput(result=input.a + input.b)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    registry = ToolRegistry()
    registry.register(AddTool())

    llm_adapter = OpenAIAdapter()  # reads OPENAI_API_KEY from env
    engine = ExecutionEngine(llm_adapter=llm_adapter, tool_registry=registry)

    # --- Tool task ---
    tool_task = Task(
        task_id="task-tool-001",
        type="tool",
        input={"tool_name": "add", "tool_input": {"a": 7, "b": 3}},
    )
    tool_result = await engine.execute_task(tool_task)
    print("=== Tool Task ===")
    print(f"Status  : {tool_result.status}")
    print(f"Output  : {tool_result.output}")
    print(f"Duration: {tool_result.duration_ms} ms")
    print()

    # --- LLM task ---
    llm_task = Task(
        task_id="task-llm-001",
        type="llm",
        input={"prompt": "Say hello in exactly three words.", "model": "gpt-4o-mini"},
    )
    llm_result = await engine.execute_task(llm_task)
    print("=== LLM Task ===")
    print(f"Status  : {llm_result.status}")
    print(f"Output  : {llm_result.output}")
    print(f"Duration: {llm_result.duration_ms} ms")
    if llm_result.trace:
        print(f"Tokens  : {llm_result.trace.token_usage}")


if __name__ == "__main__":
    asyncio.run(main())
