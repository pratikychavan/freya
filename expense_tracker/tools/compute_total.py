from __future__ import annotations

from pydantic import BaseModel

from freya import ExecutionContext, Tool


class ComputeTotalInput(BaseModel):
    amounts: list[float]


class ComputeTotalOutput(BaseModel):
    total: float
    count: int
    average: float


class ComputeTotalTool(Tool):
    """Sums a list of amounts and returns total, count, and average."""

    name = "compute_total"
    input_model = ComputeTotalInput
    output_model = ComputeTotalOutput

    async def execute(
        self, input: ComputeTotalInput, context: ExecutionContext
    ) -> ComputeTotalOutput:
        total = sum(input.amounts)
        count = len(input.amounts)
        average = total / count if count else 0.0
        return ComputeTotalOutput(total=total, count=count, average=round(average, 2))
