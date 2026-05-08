from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class DelegationContract(BaseModel):
    """Explicit governance contract for a delegated subworkflow.

    Captures:
    - *why* delegation is happening (delegation_reason)
    - *what* capabilities the child needs (required_capabilities)
    - *what* outputs are expected (expected_outputs)
    - *how* success is judged (success_criteria)
    - *what* to do on failure (failure_handling)
    - *how many* iterations the child may run (max_iterations)
    - *governance constraints* inherited from parent (governance_constraints)
    """

    contract_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_session_id: str
    child_session_id: str | None = None
    delegation_reason: str
    delegated_goal: str
    required_capabilities: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    failure_handling: str = "observe_and_continue"
    max_iterations: int | None = None
    max_runtime_seconds: int | None = None
    governance_constraints: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
