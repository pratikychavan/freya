"""freya/runtime/runtime.py

FreyaRuntime — autonomous workflow orchestration entry point.

execute_objective() pipeline:
  1. WorkflowPlanner  — parse objective → WorkflowPlan
  2. WorkflowRuntime  — execute plan phase-by-phase with registered agents
  3. CapabilityMemory — store workflow record for future recall
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from freya.agents import (
    AgentRunnerAgent,
    AnalysisAgent,
    AuditAgent,
    CapacityAgent,
    CodegenAgent,
    ComplianceAgent,
    DeliveryAgent,
    DocumentReaderAgent,
    ImplementationAgent,
    InfrastructureAgent,
    NotificationAgent,
    OperationalAgent,
    RecoveryAgent,
    ReportDispatchAgent,
    RequirementsAgent,
    RiskAgent,
    RollbackAgent,
    ScenarioGeneratorAgent,
    SummaryAgent,
    TestRunnerAgent,
    ValidationAgent,
)
from freya.memory import CapabilityMemory
from freya.workflows import WorkflowPlanner, WorkflowPlan, WorkflowResult, WorkflowRuntime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default agent registry
# ---------------------------------------------------------------------------

_DEFAULT_AGENTS: dict[str, OperationalAgent] = {
    # operational domains
    "compliance":      ComplianceAgent(),
    "risk":            RiskAgent(),
    "recovery":        RecoveryAgent(),
    "infrastructure":  InfrastructureAgent(),
    "audit":           AuditAgent(),
    "notification":    NotificationAgent(),
    "capacity":        CapacityAgent(),
    "rollback":        RollbackAgent(),
    # qa / document domains
    "document_reader": DocumentReaderAgent(),
    "test_scenario":   ScenarioGeneratorAgent(),
    "test_runner":     TestRunnerAgent(),
    "report":          ReportDispatchAgent(),
    # software / data / general domains
    "requirements":    RequirementsAgent(),
    "implementation":  ImplementationAgent(),
    "codegen":         CodegenAgent(),
    "validation":      ValidationAgent(),
    "delivery":        DeliveryAgent(),
    "agent_runner":    AgentRunnerAgent(),
    "analysis":        AnalysisAgent(),
    "summary":         SummaryAgent(),
}


# ---------------------------------------------------------------------------
# Plan type
# ---------------------------------------------------------------------------

@dataclass
class ObjectivePlan:
    """Pre-execution plan returned by FreyaRuntime.plan_objective()."""
    plan: WorkflowPlan


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class RuntimeResult:
    """Complete result of FreyaRuntime.execute_objective()."""
    objective:        str
    plan:             WorkflowPlan
    workflow_result:  WorkflowResult | None = None
    phases_completed: list[str] = field(default_factory=list)
    metrics:          dict[str, Any] = field(default_factory=dict)
    final_state:      dict[str, Any] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return (
            self.workflow_result is not None
            and self.workflow_result.final_status == "completed"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective":        self.objective,
            "succeeded":        self.succeeded,
            "domain":           self.plan.domain,
            "phases_completed": self.phases_completed,
            "metrics":          self.metrics,
            "workflow": self.workflow_result.to_dict() if self.workflow_result else None,
        }


# ---------------------------------------------------------------------------
# FreyaRuntime
# ---------------------------------------------------------------------------

class FreyaRuntime:
    """
    Autonomous workflow orchestration runtime.

    Usage:
        runtime = FreyaRuntime()
        result = await runtime.execute_objective("Create a Python calculator")
    """

    def __init__(
        self,
        agents: dict[str, OperationalAgent] | None = None,
    ) -> None:
        self._agents  = agents or dict(_DEFAULT_AGENTS)
        self._planner = WorkflowPlanner()
        self._memory  = CapabilityMemory()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan_objective(self, objective: str) -> ObjectivePlan:
        """Generate and return a plan without executing it."""
        return ObjectivePlan(plan=self._planner.plan(objective))

    async def execute_objective(
        self,
        objective: str,
        initial_state: dict[str, Any] | None = None,
    ) -> RuntimeResult:
        """
        Execute a free-text objective end-to-end and return a RuntimeResult.

        Args:
            objective:     Natural language objective.
            initial_state: Optional pre-populated workflow state.

        Returns:
            RuntimeResult with execution record and metrics.
        """
        t0     = time.monotonic()
        run_id = str(uuid4())
        logger.info("[FreyaRuntime] Objective: %s", objective)

        # Step 1 — Plan
        plan = self._planner.plan(objective)
        logger.info("[FreyaRuntime] Domain: %s  Phases: %s", plan.domain, plan.phase_names)

        # Step 2 — Execute
        wf_runtime      = WorkflowRuntime(agents=self._agents)
        workflow_result = await wf_runtime.execute(plan, initial_state=initial_state)

        # Step 3 — Persist to memory
        elapsed_ms = (time.monotonic() - t0) * 1000
        self._memory.store_workflow(
            record_id=run_id,
            objective=objective,
            domain=plan.domain,
            plan_summary=plan.to_dict(),
            outcome=workflow_result.final_status,
            elapsed_ms=elapsed_ms,
            tools_used=list(plan.agents),
        )

        phases_completed = [
            pr.phase_name for pr in workflow_result.phase_results if pr.succeeded
        ]

        return RuntimeResult(
            objective=objective,
            plan=plan,
            workflow_result=workflow_result,
            phases_completed=phases_completed,
            metrics={
                "elapsed_ms":       elapsed_ms,
                "phases_total":     len(plan.phases),
                "phases_completed": len(phases_completed),
            },
            final_state=workflow_result.state,
        )

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_playbooks(self, domain: str | None = None) -> list[dict[str, Any]]:
        """Return known playbooks, optionally filtered by domain."""
        from dataclasses import asdict
        return [asdict(p) for p in self._memory.get_playbooks(domain=domain)]

    def recall_similar(self, objective: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Return workflows similar to the given objective."""
        from dataclasses import asdict
        return [asdict(r) for r in self._memory.retrieve_similar_objectives(objective, top_k=top_k)]
