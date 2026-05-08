from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel


class PolicyResult(BaseModel):
    action: Literal["ALLOW", "BLOCK", "WARN"]
    reason: str | None = None
    policy_name: str | None = None


class Policy(ABC):
    @abstractmethod
    def check_input(self, task: dict[str, Any], context: dict[str, Any]) -> PolicyResult: ...

    @abstractmethod
    def check_output(
        self, task: dict[str, Any], result: dict[str, Any], context: dict[str, Any]
    ) -> PolicyResult: ...
