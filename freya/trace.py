from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Trace(BaseModel):
    task_id: str
    start_time: datetime
    end_time: datetime
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    error: str | None = None
    token_usage: dict[str, Any] | None = None

    @property
    def duration_ms(self) -> int:
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() * 1000)

    @classmethod
    def start(cls, task_id: str, input: dict[str, Any]) -> "Trace":
        return cls(
            task_id=task_id,
            start_time=datetime.now(tz=timezone.utc),
            end_time=datetime.now(tz=timezone.utc),
            input=input,
        )

    def finish(
        self,
        output: dict[str, Any] | None = None,
        error: str | None = None,
        token_usage: dict[str, Any] | None = None,
    ) -> None:
        self.end_time = datetime.now(tz=timezone.utc)
        self.output = output
        self.error = error
        self.token_usage = token_usage
