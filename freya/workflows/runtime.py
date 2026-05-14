"""freya/workflows/runtime.py

WorkflowRuntime — executes a WorkflowPlan phase-by-phase, dispatching
agents concurrently within each phase and collecting results.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from freya.agents.base import AgentContext, AgentResult, AgentStatus, OperationalAgent
from freya.workflows.plan import WorkflowPhase, WorkflowPlan

logger = logging.getLogger(__name__)


@dataclass
class PhaseResult:
    phase_name:    str
    agent_results: list[AgentResult]
    succeeded:     bool
    elapsed_ms:    float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase":      self.phase_name,
            "succeeded":  self.succeeded,
            "elapsed_ms": self.elapsed_ms,
            "agents":     [r.to_dict() for r in self.agent_results],
        }


@dataclass
class WorkflowResult:
    plan:          WorkflowPlan
    run_id:        str
    phase_results: list[PhaseResult] = field(default_factory=list)
    final_status:  str = "in_progress"
    state:         dict[str, Any] = field(default_factory=dict)
    errors:        list[str] = field(default_factory=list)
    elapsed_ms:    float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id":       self.run_id,
            "objective":    self.plan.objective,
            "domain":       self.plan.domain,
            "final_status": self.final_status,
            "elapsed_ms":   self.elapsed_ms,
            "phases":       [r.to_dict() for r in self.phase_results],
            "errors":       self.errors,
        }


class WorkflowRuntime:
    """
    Executes a WorkflowPlan sequentially through its phases.

    Each phase dispatches all required agents concurrently.
    Results from earlier phases are available to later phases via
    the shared state dict (keyed by agent domain).
    """

    def __init__(self, agents: dict[str, OperationalAgent]) -> None:
        self._agents = agents

    async def execute(
        self,
        plan: WorkflowPlan,
        initial_state: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """Execute all phases and return a WorkflowResult."""
        t0    = time.monotonic()
        state = dict(initial_state or {})
        state.setdefault("_objective", plan.objective)  # agents can read the real objective
        result = WorkflowResult(plan=plan, run_id=str(uuid4()), state=state)

        for phase in plan.phases:
            phase_result = await self._execute_phase(phase, state)
            result.phase_results.append(phase_result)

            for ar in phase_result.agent_results:
                state[ar.domain] = ar.output

            if not phase_result.succeeded:
                result.errors.append(f"Phase '{phase.name}' failed.")

        result.final_status = "completed" if not result.errors else "failed"
        result.elapsed_ms   = (time.monotonic() - t0) * 1000
        result.state        = state
        return result

    async def _execute_phase(
        self,
        phase: WorkflowPhase,
        state: dict[str, Any],
    ) -> PhaseResult:
        t0    = time.monotonic()
        tasks = [self._run_agent(domain, phase, state) for domain in phase.required_agent_domains]
        agent_results: list[AgentResult] = list(await asyncio.gather(*tasks))
        succeeded = all(
            ar.status in (AgentStatus.SUCCEEDED, AgentStatus.SKIPPED)
            for ar in agent_results
        )
        return PhaseResult(
            phase_name=phase.name,
            agent_results=agent_results,
            succeeded=succeeded,
            elapsed_ms=(time.monotonic() - t0) * 1000,
        )

    async def _run_agent(
        self,
        domain: str,
        phase: WorkflowPhase,
        state: dict[str, Any],
    ) -> AgentResult:
        agent = self._agents.get(domain)
        if agent is None:
            logger.warning("No agent registered for domain '%s'; skipping.", domain)
            return AgentResult(
                agent_name=f"unknown:{domain}",
                domain=domain,
                status=AgentStatus.SKIPPED,
                narration=f"No agent registered for domain '{domain}'.",
            )
        ctx = AgentContext(
            objective=phase.description,
            phase_name=phase.name,
            state=state,
        )
        return await agent.execute(ctx)
