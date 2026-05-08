from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Task(BaseModel):
    task_id: str
    type: Literal["llm", "tool"]
    input: dict[str, Any]
    config: dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    task_id: str
    status: Literal["SUCCESS", "FAILED"]
    output: dict[str, Any] | None = None
    error: str | None = None
    error_type: str | None = None
    duration_ms: int
    trace: "Trace | None" = None

    model_config = {"arbitrary_types_allowed": True}


from freya.trace import Trace  # noqa: E402 — deferred to avoid circular import

TaskResult.model_rebuild()
