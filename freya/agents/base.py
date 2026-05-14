"""freya/agents/base.py

Abstract base class for SDK-level operational agents.
Agents wrap Freya internal pipelines and expose a uniform
execute() interface to the WorkflowRuntime.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    SUCCEEDED = "succeeded"
    FAILED    = "failed"
    SKIPPED   = "skipped"


@dataclass
class AgentContext:
    """Runtime context passed to every agent execution."""
    objective:    str
    phase_name:   str
    state:        dict[str, Any]
    metadata:     dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result returned by an agent execution."""
    agent_name:    str
    domain:        str
    status:        AgentStatus
    output:        dict[str, Any] = field(default_factory=dict)
    narration:     str = ""
    errors:        list[str] = field(default_factory=list)
    warnings:      list[str] = field(default_factory=list)
    elapsed_ms:    float = 0.0

    @property
    def succeeded(self) -> bool:
        return self.status == AgentStatus.SUCCEEDED

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent":     self.agent_name,
            "domain":    self.domain,
            "status":    self.status,
            "narration": self.narration,
            "output":    self.output,
            "errors":    self.errors,
            "warnings":  self.warnings,
            "elapsed_ms": self.elapsed_ms,
        }


class OperationalAgent(ABC):
    """
    Abstract base for SDK operational agents.

    Each agent is responsible for exactly one domain.
    Agents operate on the shared workflow state dictionary
    and return a structured AgentResult.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name."""

    @property
    @abstractmethod
    def domain(self) -> str:
        """Operational domain this agent covers."""

    @property
    def description(self) -> str:
        """Optional human-readable description."""
        return f"{self.domain} operational agent"

    @abstractmethod
    async def execute(
        self,
        context: AgentContext,
    ) -> AgentResult:
        """
        Execute the agent's logic given the current workflow context.

        Must not raise — return AgentResult with status=FAILED on errors.
        """

    async def run(self, prompt: str, **state_overrides: Any) -> AgentResult:
        """Call the agent directly with a natural-language prompt."""
        ctx = AgentContext(
            objective=prompt,
            phase_name="prompt",
            state=dict(state_overrides),
        )
        return await self.execute(ctx)

    def _result(
        self,
        status: AgentStatus,
        output: dict[str, Any] | None = None,
        narration: str = "",
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        elapsed_ms: float = 0.0,
    ) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            domain=self.domain,
            status=status,
            output=output or {},
            narration=narration,
            errors=errors or [],
            warnings=warnings or [],
            elapsed_ms=elapsed_ms,
        )
