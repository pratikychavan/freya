"""
Step 5 — Policy Layer example.

Three tasks:
  task-allowed : tool task with all required fields → ALLOW
  task-blocked : LLM task with over-length prompt → BLOCK (never executes)
  task-warned  : LLM task with flagged keyword → WARN (still executes)

Run (no API key needed — LLM tasks are mocked):
    python examples/policy_example.py
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock

from pydantic import BaseModel

from freya.dag import DAG, DAGRunner, DAGTask
from freya.engine import ExecutionEngine
from freya.policy import MaxLengthPolicy, PolicyManager, PromptKeywordPolicy, RequiredFieldPolicy
from freya.registry import ToolRegistry
from freya.tool import Tool
from freya.tools import AddNumbersTool


# ---------------------------------------------------------------------------
# Mock LLM that just echoes the prompt back
# ---------------------------------------------------------------------------

def make_engine(registry: ToolRegistry, policy_manager: PolicyManager) -> ExecutionEngine:
    mock_llm = AsyncMock()
    mock_llm.complete = AsyncMock(
        return_value={"text": "mocked response", "usage": {"total_tokens": 10}}
    )
    return ExecutionEngine(
        llm_adapter=mock_llm,
        tool_registry=registry,
        policy_manager=policy_manager,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    registry = ToolRegistry()
    registry.register(AddNumbersTool())

    policy_manager = PolicyManager()
    policy_manager.add_policy(MaxLengthPolicy(max_chars=50))
    policy_manager.add_policy(RequiredFieldPolicy(required_fields=["a", "b"]))
    policy_manager.add_policy(PromptKeywordPolicy(keywords=["secret", "password"]))

    engine = make_engine(registry, policy_manager)
    runner = DAGRunner(engine=engine)

    dag = DAG(
        tasks=[
            # ALLOW: valid tool task with required fields present
            DAGTask(
                task_id="task-allowed",
                type="tool",
                input={"tool_name": "add_numbers", "tool_input": {"a": 4, "b": 6}},
            ),
            # BLOCK: LLM prompt exceeds 50-char limit
            DAGTask(
                task_id="task-blocked",
                type="llm",
                input={
                    "prompt": "This is a very long prompt that definitely exceeds fifty characters total.",
                    "model": "gpt-4o-mini",
                },
            ),
            # WARN: prompt contains flagged keyword but still executes
            DAGTask(
                task_id="task-warned",
                type="llm",
                input={"prompt": "Tell me a secret fact.", "model": "gpt-4o-mini"},
            ),
        ]
    )

    dag_result = await runner.run(dag)

    print(f"\n{'='*60}")
    print(f"  DAG status: {dag_result.status}")
    print(f"{'='*60}\n")

    for task_id, result in dag_result.results.items():
        print(f"  [{task_id}]  {result.status}")
        if result.output:
            print(f"    output : {result.output}")
        if result.error:
            print(f"    error  : {result.error.splitlines()[0]}")

    # Show policy_check events from the trace
    if dag_result.dag_trace:
        print("\n--- Policy Events in Trace ---")
        for tid, tt in dag_result.dag_trace.task_traces.items():
            policy_events = [e for e in tt.events if e.event_type == "policy_check"]
            if policy_events:
                print(f"\n  {tid}:")
                for ev in policy_events:
                    p = ev.payload
                    line = f"    [{p['stage']}] {p['policy_name']}  →  {p['action']}"
                    if p.get("reason"):
                        line += f"  — {p['reason']}"
                    print(line)


if __name__ == "__main__":
    asyncio.run(main())
