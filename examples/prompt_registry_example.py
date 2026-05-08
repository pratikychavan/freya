"""
Prompt Registry example.

Demonstrates:
  - Registering named prompt templates
  - Variable injection at retrieval time
  - Running LLM tasks via prompt_name + variables (no raw prompt string)
  - Trace events: prompt_name, template, variables, rendered_prompt logged automatically

Run:
    python examples/prompt_registry_example.py
"""

from __future__ import annotations

import asyncio
import json
import logging
from unittest.mock import AsyncMock

from freya import (
    ExecutionEngine,
    Prompt,
    PromptRegistry,
    Task,
    ToolRegistry,
    TraceManager,
)

logging.basicConfig(level=logging.WARNING, format="%(levelname)-8s  %(message)s")


# ---------------------------------------------------------------------------
# Register prompts
# ---------------------------------------------------------------------------

def build_registry() -> PromptRegistry:
    pr = PromptRegistry()

    pr.register(
        "summarize_v1",
        Prompt(
            template="Summarize the following:\n{text}",
            system="You are a concise summarisation assistant.",
            metadata={"version": 1, "author": "freya-team"},
        ),
    )

    pr.register(
        "explain_number",
        Prompt(
            template="Explain what the number {value} represents in simple terms.",
        ),
    )

    pr.register(
        "greet_user",
        Prompt(
            template="Write a friendly greeting for a user named {name} who works as a {role}.",
            variables={"role": "developer"},   # default variable — overridable at get() time
        ),
    )

    return pr


# ---------------------------------------------------------------------------
# Run tasks through the engine
# ---------------------------------------------------------------------------

async def main() -> None:
    registry = build_registry()

    # Mock LLM — echoes back the rendered prompt so we can verify it
    llm = AsyncMock()
    llm.complete.side_effect = lambda req: {
        "text": f"[LLM response to]: {req.get('prompt', '')}",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }

    engine = ExecutionEngine(
        llm_adapter=llm,
        tool_registry=ToolRegistry(),
        prompt_registry=registry,
    )

    print("Registered prompts:", registry.list_prompts())
    print()

    tasks = [
        Task(
            task_id="t-summarise",
            type="llm",
            input={
                "prompt_name": "summarize_v1",
                "variables": {"text": "The Freya SDK is a production-grade agent execution framework."},
                "model": "gpt-4o-mini",
            },
        ),
        Task(
            task_id="t-explain",
            type="llm",
            input={
                "prompt_name": "explain_number",
                "variables": {"value": 42},
            },
        ),
        Task(
            task_id="t-greet-default",
            type="llm",
            input={
                "prompt_name": "greet_user",
                "variables": {"name": "Alice"},
                # role uses the registered default: "developer"
            },
        ),
        Task(
            task_id="t-greet-override",
            type="llm",
            input={
                "prompt_name": "greet_user",
                "variables": {"name": "Bob", "role": "data scientist"},
                # overrides the default role
            },
        ),
    ]

    print("=" * 60)
    for task in tasks:
        tm = TraceManager()
        result = await engine.execute_task(task, trace_manager=tm)
        tm.finalize(result.status)

        print(f"\n[{task.task_id}]  status={result.status}")
        if result.output:
            print(f"  LLM output : {result.output.get('text')}")

        # Show trace event with rendered prompt
        task_trace = tm.dag_trace.task_traces.get(task.task_id)
        if task_trace:
            for ev in task_trace.events:
                if ev.event_type == "llm_call_started" and "rendered_prompt" in ev.payload:
                    p = ev.payload
                    print(f"  prompt_name    : {p['prompt_name']}")
                    print(f"  template       : {p['template']!r}")
                    print(f"  variables      : {p['variables']}")
                    print(f"  rendered       : {p['rendered_prompt']!r}")

    # --- Duplicate registration error ---
    print("\n" + "=" * 60)
    print("\nDuplicate registration:")
    try:
        registry.register("summarize_v1", Prompt(template="duplicate"))
    except ValueError as e:
        print(f"  Caught expected error → {e}")

    # --- Missing prompt error ---
    print("\nMissing prompt retrieval:")
    try:
        registry.get("nonexistent_prompt")
    except KeyError as e:
        print(f"  Caught expected error → {e}")


if __name__ == "__main__":
    asyncio.run(main())
