from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from freya.tool import Tool

if TYPE_CHECKING:
    from freya.context import ExecutionContext


class AddNumbersInput(BaseModel):
    a: int
    b: int


class AddNumbersOutput(BaseModel):
    result: int


class AddNumbersTool(Tool):
    name = "add_numbers"
    input_model = AddNumbersInput
    output_model = AddNumbersOutput

    async def execute(self, input: AddNumbersInput, context: "ExecutionContext") -> AddNumbersOutput:  # type: ignore[override]
        return AddNumbersOutput(result=input.a + input.b)
