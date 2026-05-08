from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, model_validator

from freya.models import TaskResult
from freya.tracing.models import DAGTrace


class DAGTask(BaseModel):
    task_id: str
    type: Literal["llm", "tool", "subworkflow"]
    input: dict[str, Any]
    depends_on: list[str] = []
    config: dict[str, Any] = {}


class DAG(BaseModel):
    tasks: list[DAGTask]

    @model_validator(mode="after")
    def _unique_ids(self) -> "DAG":
        ids = [t.task_id for t in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("DAG contains duplicate task_id values.")
        return self


class DAGResult(BaseModel):
    results: dict[str, TaskResult]
    status: Literal["SUCCESS", "FAILED"]
    dag_trace: DAGTrace | None = None

    model_config = {"arbitrary_types_allowed": True}
