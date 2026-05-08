from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "task_started",
    "task_completed",
    "task_failed",
    "llm_call_started",
    "llm_call_completed",
    "tool_call_started",
    "tool_call_completed",
    "policy_check",
    "memory_access",
]


class TraceEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    event_type: EventType
    task_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskTrace(BaseModel):
    task_id: str
    start_time: float
    end_time: float | None = None
    status: Literal["SUCCESS", "FAILED"] = "SUCCESS"
    events: list[TraceEvent] = Field(default_factory=list)
    error: str | None = None
    token_usage: dict[str, Any] | None = None

    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000


class DAGTrace(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_traces: dict[str, TaskTrace] = Field(default_factory=dict)
    start_time: float = Field(default_factory=time.time)
    end_time: float | None = None
    status: Literal["SUCCESS", "FAILED"] = "SUCCESS"
