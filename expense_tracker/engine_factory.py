from __future__ import annotations

from unittest.mock import AsyncMock

from freya import ExecutionEngine, PolicyManager, PromptRegistry, ToolRegistry

from expense_tracker.tools.record_expenses import RecordExpensesTool
from expense_tracker.tools.compute_total import ComputeTotalTool
from expense_tracker.tools.format_report import FormatReportTool
from expense_tracker.policies.expense_policy import ExpenseAmountPolicy
from expense_tracker.prompts import build_prompt_registry


def make_engine() -> ExecutionEngine:
    registry = ToolRegistry()
    registry.register(RecordExpensesTool())
    registry.register(ComputeTotalTool())
    registry.register(FormatReportTool())

    pm = PolicyManager()
    pm.add_policy(ExpenseAmountPolicy(max_single_amount=500.0, max_total_amount=2000.0))

    llm = AsyncMock()
    llm.complete.side_effect = lambda req: {
        "text": (
            "APPROVED — All items are within policy limits and total is reasonable."
            if "approve" in req.get("prompt", "").lower() or "review" in req.get("prompt", "").lower()
            else "3 expenses totalling $100.00 submitted for manager review."
        ),
        "usage": {"prompt_tokens": 40, "completion_tokens": 20, "total_tokens": 60},
    }

    prompt_registry = build_prompt_registry()

    return ExecutionEngine(
        llm_adapter=llm,
        tool_registry=registry,
        policy_manager=pm,
        prompt_registry=prompt_registry,
    )
