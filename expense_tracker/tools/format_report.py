from __future__ import annotations

from pydantic import BaseModel

from freya import ExecutionContext, Tool


class ReportLine(BaseModel):
    category: str
    amount: float


class FormatReportInput(BaseModel):
    lines: list[ReportLine]
    total: float
    currency: str = "USD"


class FormatReportOutput(BaseModel):
    report: str


class FormatReportTool(Tool):
    """Renders a formatted plain-text expense report."""

    name = "format_report"
    input_model = FormatReportInput
    output_model = FormatReportOutput

    async def execute(
        self, input: FormatReportInput, context: ExecutionContext
    ) -> FormatReportOutput:
        symbol = "$" if input.currency == "USD" else input.currency
        width = max(len(line.category) for line in input.lines) + 2
        separator = "─" * (width + 14)
        rows = "\n".join(
            f"  {line.category:<{width}}  {symbol}{line.amount:>8.2f}"
            for line in input.lines
        )
        report = (
            f"Expense Report\n"
            f"{separator}\n"
            f"{rows}\n"
            f"{separator}\n"
            f"  {'Total':<{width}}  {symbol}{input.total:>8.2f}\n"
            f"  {'Items':<{width}}  {len(input.lines)}\n"
            f"  {'Average':<{width}}  {symbol}{input.total / len(input.lines):>8.2f}\n"
        )
        return FormatReportOutput(report=report)
