"""
Expense Tracker — entry point.

All tool classes, engine setup, and runner logic live under:

    expense_tracker/
    ├── __init__.py
    ├── data.py                     — shared EXPENSES / AMOUNTS constants
    ├── engine_factory.py           — builds ExecutionEngine + registry + policy
    ├── runner.py                   — run_as_dag() and run_as_worker() coroutines
    └── tools/
        ├── __init__.py
        ├── record_expenses.py      — RecordExpensesTool
        ├── compute_total.py        — ComputeTotalTool
        └── format_report.py        — FormatReportTool

Run:
    python examples/run_expense_tracker.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

from expense_tracker.runner import run_as_dag, run_as_worker


async def main() -> None:
    await run_as_dag()
    # await run_as_worker()


if __name__ == "__main__":
    asyncio.run(main())
