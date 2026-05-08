from __future__ import annotations

import json

from freya import DAG, DAGRunner, DAGTask, Worker
from freya.transport import MockTransport

from expense_tracker.data import AMOUNTS, EXPENSES
from expense_tracker.engine_factory import make_engine

_REPORT_LINES = "\n".join(
    f"  {e['category']}: ${e['amount']:.2f}" for e in EXPENSES
)


async def run_as_dag() -> None:
    print("\n" + "=" * 60)
    print("  Option A: DAG Runner  (parallel steps + LLM approval)")
    print("=" * 60)

    engine = make_engine()
    runner = DAGRunner(engine)

    dag = DAG(tasks=[
        DAGTask(
            task_id="step_record",
            type="tool",
            input={
                "tool_name": "record_expenses",
                "tool_input": {"expenses": EXPENSES},
            },
        ),
        DAGTask(
            task_id="step_total",
            type="tool",
            input={
                "tool_name": "compute_total",
                "tool_input": {"amounts": AMOUNTS},
            },
        ),
        DAGTask(
            task_id="step_report",
            type="tool",
            depends_on=["step_record", "step_total"],
            input={
                "tool_name": "format_report",
                "tool_input": {
                    "lines": EXPENSES,
                    "total": sum(AMOUNTS),
                    "currency": "USD",
                },
            },
        ),
        # LLM task: uses PromptRegistry — no raw prompt string
        DAGTask(
            task_id="step_approve",
            type="llm",
            depends_on=["step_report"],
            input={
                "prompt_name": "expense_approval_request",
                "variables": {"report": _REPORT_LINES, "total": sum(AMOUNTS)},
                "model": "gpt-4o-mini",
            },
        ),
        DAGTask(
            task_id="step_summary",
            type="llm",
            depends_on=["step_report"],
            input={
                "prompt_name": "expense_summary",
                "variables": {"report": _REPORT_LINES},
                "model": "gpt-4o-mini",
            },
        ),
    ])

    result = await runner.run(dag)

    print(f"\nDAG status : {result.status}")
    for task_id, tr in result.results.items():
        icon = "✓" if tr.status == "SUCCESS" else "✗"
        preview = json.dumps(tr.output)[:70] if tr.output else (tr.error or "")[:70]
        print(f"  [{icon}] {task_id:<16}  {preview}")

    report_text = result.results["step_report"].output.get("report", "")
    print(f"\n{report_text}")
    print(f"Approval  : {result.results['step_approve'].output.get('text', '')}")
    print(f"Summary   : {result.results['step_summary'].output.get('text', '')}")

    if result.dag_trace:
        events = sum(len(t.events) for t in result.dag_trace.task_traces.values())
        print(f"\nTrace: {len(result.dag_trace.task_traces)} tasks, {events} events")

        # Show rendered prompts from trace
        print("\n--- Prompt trace ---")
        for task_id, tt in result.dag_trace.task_traces.items():
            for ev in tt.events:
                if ev.event_type == "llm_call_started" and "prompt_name" in ev.payload:
                    p = ev.payload
                    print(f"  [{task_id}] prompt='{p['prompt_name']}'  rendered={p['rendered_prompt'][:60]!r}...")


async def run_as_worker() -> None:
    print("\n" + "=" * 60)
    print("  Option B: Worker + MockTransport  (sequential session)")
    print("=" * 60)

    engine = make_engine()
    transport = MockTransport()

    transport.push_task({
        "task_id": "w_record",
        "session_id": "expense-session",
        "type": "tool",
        "input": {
            "tool_name": "record_expenses",
            "tool_input": {"expenses": EXPENSES},
        },
    })
    transport.push_task({
        "task_id": "w_total",
        "session_id": "expense-session",
        "type": "tool",
        "input": {
            "tool_name": "compute_total",
            "tool_input": {"amounts": AMOUNTS},
        },
    })
    transport.push_task({
        "task_id": "w_report",
        "session_id": "expense-session",
        "type": "tool",
        "input": {
            "tool_name": "format_report",
            "tool_input": {
                "lines": EXPENSES,
                "total": sum(AMOUNTS),
                "currency": "USD",
            },
        },
    })
    transport.push_task({
        "task_id": "w_approve",
        "session_id": "expense-session",
        "type": "llm",
        "input": {
            "prompt_name": "expense_approval_request",
            "variables": {"report": _REPORT_LINES, "total": sum(AMOUNTS)},
            "model": "gpt-4o-mini",
        },
    })
    transport.push_task({
        "task_id": "w_summary",
        "session_id": "expense-session",
        "type": "llm",
        "is_terminal": True,
        "input": {
            "prompt_name": "expense_summary",
            "variables": {"report": _REPORT_LINES},
            "model": "gpt-4o-mini",
        },
    })

    worker = Worker(
        worker_id="worker-1",
        transport=transport,
        engine=engine,
        poll_interval=0,
    )
    await worker.run(max_iterations=8)

    results = transport.all_results()
    print(f"\nWorker processed {len(results)} tasks\n")

    for task_id in ("w_record", "w_total", "w_report", "w_approve", "w_summary"):
        r = results.get(task_id, {})
        icon = "✓" if r.get("status") == "SUCCESS" else "✗"
        output_preview = json.dumps(r.get("output") or {})[:70]
        print(f"  [{icon}] {task_id:<12}  {output_preview}")

    report_text = results.get("w_report", {}).get("output", {}).get("report", "")
    if report_text:
        print(f"\n{report_text}")
    print(f"Approval  : {results.get('w_approve', {}).get('output', {}).get('text', '')}")
    print(f"Summary   : {results.get('w_summary', {}).get('output', {}).get('text', '')}")

    remaining = worker._memory.list_keys("expense-session")
    print(f"\nMemory after cleanup : {remaining if remaining else '(empty — correctly cleaned up)'}")