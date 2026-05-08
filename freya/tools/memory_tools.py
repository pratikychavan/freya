from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from freya.context import ExecutionContext
from freya.tool import Tool


# ---------------------------------------------------------------------------
# StoreValueTool
# ---------------------------------------------------------------------------

class StoreValueInput(BaseModel):
    key: str
    value: Any


class StoreValueOutput(BaseModel):
    status: str


class StoreValueTool(Tool):
    name = "store_value"
    input_model = StoreValueInput
    output_model = StoreValueOutput

    async def execute(self, input: StoreValueInput, context: ExecutionContext) -> StoreValueOutput:  # type: ignore[override]
        context.memory.set(context.session_id, input.key, input.value)
        return StoreValueOutput(status="stored")


# ---------------------------------------------------------------------------
# GetValueTool
# ---------------------------------------------------------------------------

class GetValueInput(BaseModel):
    key: str


class GetValueOutput(BaseModel):
    value: Any


class GetValueTool(Tool):
    name = "get_value"
    input_model = GetValueInput
    output_model = GetValueOutput

    async def execute(self, input: GetValueInput, context: ExecutionContext) -> GetValueOutput:  # type: ignore[override]
        value = context.memory.get(context.session_id, input.key)
        return GetValueOutput(value=value)
