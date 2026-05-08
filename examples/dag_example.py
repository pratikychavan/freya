"""
DAG example:

  Task A  ──┐
            ├──► Task B (tool, depends on A)
  Task C  ──┘

A and C run in parallel (no deps).
B runs after A completes and receives A's output merged into its input.

Run:
    OPENAI_API_KEY=sk-... python examples/dag_example.py
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pydantic import BaseModel

from freya.adapters.openai import OpenAIAdapter
from freya.dag import DAG, DAGRunner, DAGTask
from freya.engine import ExecutionEngine
from freya.registry import ToolRegistry
from freya.tool import Tool

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")


# ---------------------------------------------------------------------------
# Sample tool: echoes its input back with a "processed" flag
# ---------------------------------------------------------------------------

class EchoInput(BaseModel):
    model_config = {"extra": "allow"}


class EchoOutput(BaseModel):
    echoed: dict[str, Any]
    processed: bool


class EchoTool(Tool):
    name = "echo"
    input_model = EchoInput
    output_model = EchoOutput

    async def execute(self, input: EchoInput, context) -> EchoOutput:  # type: ignore[override]
        return EchoOutput(echoed=input.model_dump(), processed=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    llm = OpenAIAdapter()
    engine = ExecutionEngine(llm_adapter=llm, tool_registry=registry)
    runner = DAGRunner(engine=engine)

    dag = DAG(
        tasks=[
            # Task A — LLM, no dependencies (runs in parallel with C)
            DAGTask(
                task_id="A",
                type="llm",
                input={"prompt": "Reply with exactly: hello from A", "model": "gpt-4o-mini"},
            ),
            # Task C — LLM, no dependencies (runs in parallel with A)
            DAGTask(
                task_id="C",
                type="llm",
                input={"prompt": "Reply with exactly: hello from C", "model": "gpt-4o-mini"},
            ),
            # Task B — tool, depends on A (runs after A; A's output merged into input)
            DAGTask(
                task_id="B",
                type="tool",
                input={"tool_name": "echo", "tool_input": {"note": "I got A's result"}},
                depends_on=["A"],
            ),
        ]
    )

    dag_result = await runner.run(dag)

    print(f"\n=== DAG Status: {dag_result.status} ===\n")
    for task_id, result in dag_result.results.items():
        print(f"  [{task_id}] {result.status}  ({result.duration_ms} ms)")
        print(f"       output : {result.output}")
        if result.error:
            print(f"       error  : {result.error[:120]}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
