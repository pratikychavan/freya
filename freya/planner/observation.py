from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """A single runtime observation produced after a task completes."""

    task_id: str
    task_type: str
    status: str
    output: dict[str, Any] | None = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    semantic_summary: str | None = None
    repair_attempted: bool = False
    repair_reason: str | None = None
    # Runtime failure recovery fields
    failure_category: str | None = None
    recoverable: bool = False
    recovery_attempted: bool = False

    @classmethod
    def from_task_result(
        cls,
        task_id: str,
        task_type: str,
        status: str,
        output: dict[str, Any] | None,
        error: str | None,
        semantic_summary: str | None = None,
        failure_category: str | None = None,
        recoverable: bool = False,
    ) -> "Observation":
        return cls(
            task_id=task_id,
            task_type=task_type,
            status=status,
            output=output,
            error=error,
            semantic_summary=semantic_summary,
            failure_category=failure_category,
            recoverable=recoverable,
        )

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict (all datetimes as ISO strings)."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Observation":
        """Reconstruct from a previously serialized dict."""
        return cls.model_validate(data)

    def as_summary(self) -> str:
        """Produce a compact, planner-friendly one-line summary."""
        if self.recovery_attempted:
            prefix = "[RECOVERY] "
        elif self.repair_attempted:
            prefix = "[REPAIR] "
        else:
            prefix = ""
        if self.semantic_summary:
            return f"{prefix}{self.semantic_summary}"
        if self.status == "SUCCESS":
            if self.output:
                pairs = [f"{k}={repr(v)}" for k, v in list(self.output.items())[:2]]
                return f"{prefix}{self.task_id} succeeded with {', '.join(pairs)}"
            return f"{prefix}{self.task_id} succeeded (no output)"
        cat = f" [{self.failure_category}]" if self.failure_category else ""
        return f"{prefix}{self.task_id} FAILED{cat}: {(self.error or 'unknown error')[:120]}"
