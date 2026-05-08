from __future__ import annotations

from pydantic import BaseModel, field_validator

from freya import ExecutionContext, Tool


class ExpenseEntry(BaseModel):
    category: str
    amount: float

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class RecordExpensesInput(BaseModel):
    expenses: list[ExpenseEntry]


class RecordExpensesOutput(BaseModel):
    stored_keys: list[str]
    count: int


class RecordExpensesTool(Tool):
    """Validates expense entries and persists each one to session memory."""

    name = "record_expenses"
    input_model = RecordExpensesInput
    output_model = RecordExpensesOutput

    async def execute(
        self, input: RecordExpensesInput, context: ExecutionContext
    ) -> RecordExpensesOutput:
        stored_keys: list[str] = []
        for entry in input.expenses:
            key = f"expense_{entry.category.lower().replace(' ', '_')}"
            context.memory.set(context.session_id, key, entry.amount)
            stored_keys.append(key)
        return RecordExpensesOutput(stored_keys=stored_keys, count=len(stored_keys))
