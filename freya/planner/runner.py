from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from freya.dag.models import DAG, DAGTask
from freya.dag.runner import DAGRunner
from freya.memory.store import InMemoryStore, MemoryStore
from freya.planner.base import BasePlanner
from freya.planner.context import PlanningContext
from freya.planner.context_builder import build_planner_context
from freya.planner.mode import PlanningMode
from freya.planner.observation import Observation
from freya.planner.trace import PlannerEvent, PlannerTrace
from freya.planner.failure_classifier import classify_failure
from freya.planner.validation import validate_dag_fragment
from freya.registry import ToolRegistry
from freya.governance.engine import GovernanceEngine
from freya.governance.approval import ApprovalRequest
from freya.governance.errors import (
    WorkflowAlreadyResumedError,
    WorkflowLeaseError,
    WorkflowVersionConflictError,
)
from freya.governance.models import InterventionDecision
from freya.governance.state import WorkflowState
from freya.governance.store import InMemoryApprovalStore
from freya.governance.snapshot import WorkflowSnapshot
from freya.governance.persistent_store import PersistentWorkflowStore
from freya.events.models import EventType, RuntimeEvent
from freya.events.bus import InProcessEventBus
from freya.workflows.coordinator import WorkflowCoordinator
from freya.workflows.models import RelationshipType
from freya.workflows.contracts import DelegationContract
from freya.workflows.capability_validation import validate_contract_capabilities
from freya.strategies.engine import ExecutionStrategyEngine
from freya.strategies.signals import RuntimeSignals
from freya.strategies.models import ExecutionStrategy, StrategyDecision
from freya.economics.engine import ExecutionEconomicsEngine
from freya.economics.models import WorkflowBudget, WorkflowPriority

logger = logging.getLogger(__name__)

MAX_ITERATIONS: int = 10
MAX_TOTAL_TASKS: int = 50
MAX_REPAIR_ATTEMPTS: int = 1
MAX_RUNTIME_RECOVERY_ATTEMPTS: int = 2


@dataclass
class PlannerResult:
    session_id: str
    goal: str
    final_context: PlanningContext
    trace: PlannerTrace
    workflow_state: WorkflowState = WorkflowState.COMPLETED
    approval_request_id: str | None = None


class IterativePlannerRunner:
    """Drives the iterative plan → validate → execute → observe loop.

    Safety limits (hard-coded):
    - MAX_ITERATIONS    = 10
    - MAX_TOTAL_TASKS   = 50
    - MAX_REPAIR_ATTEMPTS = 1  (one retry on invalid DAG before failing)
    """

    def __init__(
        self,
        planner: BasePlanner,
        dag_runner: DAGRunner,
        tool_registry: ToolRegistry,
        memory: MemoryStore | None = None,
        planning_mode: PlanningMode = PlanningMode.DETERMINISTIC,
        prompt_capability_registry: object | None = None,
        governance_engine: GovernanceEngine | None = None,
        approval_store: InMemoryApprovalStore | None = None,
        persistent_store: PersistentWorkflowStore | None = None,
        runner_id: str | None = None,
        event_bus: InProcessEventBus | None = None,
        coordinator: WorkflowCoordinator | None = None,
        strategy_engine: ExecutionStrategyEngine | None = None,
        economics_engine: ExecutionEconomicsEngine | None = None,
    ) -> None:
        self._planner = planner
        self._dag_runner = dag_runner
        self._tool_registry = tool_registry
        self._memory = memory or InMemoryStore()
        self._planning_mode = planning_mode
        self._prompt_capability_registry = prompt_capability_registry
        self._governance = governance_engine
        self._approval_store = approval_store
        self._persistent_store = persistent_store
        self.runner_id: str = runner_id or str(uuid.uuid4())
        self._event_bus: InProcessEventBus | None = event_bus
        self._coordinator: WorkflowCoordinator | None = coordinator
        self._strategy_engine: ExecutionStrategyEngine | None = strategy_engine
        self._economics: ExecutionEconomicsEngine | None = economics_engine

    # ------------------------------------------------------------------
    # Event bus helper
    # ------------------------------------------------------------------

    async def _emit(
        self,
        event_type: str,
        session_id: str,
        iteration: int | None = None,
        workflow_state: WorkflowState | None = None,
        payload: dict | None = None,
    ) -> None:
        """Publish a RuntimeEvent to the bus if one is configured."""
        if self._event_bus is None:
            return
        await self._event_bus.publish(RuntimeEvent(
            event_type=event_type,
            session_id=session_id,
            iteration=iteration,
            workflow_state=workflow_state.value if workflow_state else None,
            payload=payload or {},
        ))

    # ------------------------------------------------------------------
    # Subworkflow execution
    # ------------------------------------------------------------------

    async def _run_subworkflow_tasks(
        self,
        sw_tasks: "list[DAGTask]",
        context: PlanningContext,
        planner_trace: PlannerTrace,
        iteration: int,
        session_id: str,
        goal: str,
    ) -> "list[Observation]":
        """Execute subworkflow tasks inline, validating delegation contracts first.

        Contract validation steps (per task):
        1. Require a contract dict in ``task.input["contract"]``
        2. Validate required capabilities against tool/prompt registries
        3. Evaluate delegation governance policies (depth, budget, missing caps)

        On validation failure the child is NOT spawned and a rejection
        observation is added to the parent context.

        Each accepted child workflow runs a full IterativePlannerRunner,
        inheriting governance, event bus, persistence, and coordinator.
        Child snapshots and leases are independent from the parent.

        Returns the list of summary Observations added to *context*.
        """
        new_obs: list[Observation] = []

        for task in sw_tasks:
            child_goal: str = task.input.get("goal", "")
            planning_mode_str: str = task.input.get("planning_mode", self._planning_mode.value)
            contract_dict: dict | None = task.input.get("contract")
            child_session_id = str(uuid.uuid4())

            # -----------------------------------------------------------------
            # Contract requirement check
            # -----------------------------------------------------------------
            if contract_dict is None:
                rejection_summary = (
                    f"delegation rejected: no contract provided for task {task.task_id}"
                )
                context.child_workflow_summaries.append(rejection_summary)
                context.failed_tasks.append(task.task_id)
                context.task_results[task.task_id] = {
                    "status": "FAILED",
                    "output": None,
                    "error": "Subworkflow delegation requires an explicit DelegationContract.",
                }
                planner_trace.events.append(PlannerEvent(
                    event_type="delegation_contract_rejected",
                    iteration=iteration,
                    payload={
                        "task_id": task.task_id,
                        "reason": "no_contract_provided",
                    },
                ))
                await self._emit(
                    EventType.DELEGATION_CONTRACT_REJECTED, session_id,
                    iteration=iteration,
                    workflow_state=WorkflowState.RUNNING,
                    payload={"task_id": task.task_id, "reason": "no_contract_provided"},
                )
                obs = Observation(
                    task_id=task.task_id,
                    task_type="subworkflow",
                    status="FAILED",
                    semantic_summary=rejection_summary,
                )
                context.recent_observations.append(obs)
                new_obs.append(obs)
                continue

            # -----------------------------------------------------------------
            # Build DelegationContract
            # -----------------------------------------------------------------
            contract = DelegationContract(
                parent_session_id=session_id,
                child_session_id=child_session_id,
                delegated_goal=child_goal,
                delegation_reason=contract_dict.get("delegation_reason", ""),
                required_capabilities=contract_dict.get("required_capabilities", []),
                expected_outputs=contract_dict.get("expected_outputs", []),
                success_criteria=contract_dict.get("success_criteria", []),
                failure_handling=contract_dict.get("failure_handling", "observe_and_continue"),
                max_iterations=contract_dict.get("max_iterations"),
                max_runtime_seconds=contract_dict.get("max_runtime_seconds"),
                governance_constraints=contract_dict.get("governance_constraints", []),
            )

            planner_trace.events.append(PlannerEvent(
                event_type="delegation_contract_created",
                iteration=iteration,
                payload={
                    "contract_id": contract.contract_id,
                    "task_id": task.task_id,
                    "delegated_goal": contract.delegated_goal,
                    "required_capabilities": contract.required_capabilities,
                },
            ))
            await self._emit(
                EventType.DELEGATION_CONTRACT_CREATED, session_id,
                iteration=iteration,
                workflow_state=WorkflowState.RUNNING,
                payload={
                    "contract_id": contract.contract_id,
                    "required_capabilities": contract.required_capabilities,
                    "parent_session_id": session_id,
                    "child_session_id": child_session_id,
                },
            )

            # -----------------------------------------------------------------
            # Capability validation
            # -----------------------------------------------------------------
            caps_valid, missing_caps = validate_contract_capabilities(
                contract,
                self._tool_registry,
                self._prompt_capability_registry,
            )
            if not caps_valid:
                rejection_summary = (
                    f"delegation rejected: missing capability "
                    + ", ".join(missing_caps)
                    + f" for task {task.task_id}"
                )
                context.child_workflow_summaries.append(rejection_summary)
                context.failed_tasks.append(task.task_id)
                context.task_results[task.task_id] = {
                    "status": "FAILED",
                    "output": None,
                    "error": rejection_summary,
                }
                planner_trace.events.append(PlannerEvent(
                    event_type="delegation_capability_missing",
                    iteration=iteration,
                    payload={
                        "contract_id": contract.contract_id,
                        "task_id": task.task_id,
                        "required_capabilities": contract.required_capabilities,
                        "missing_capabilities": missing_caps,
                    },
                ))
                await self._emit(
                    EventType.DELEGATION_CAPABILITY_MISSING, session_id,
                    iteration=iteration,
                    workflow_state=WorkflowState.RUNNING,
                    payload={
                        "contract_id": contract.contract_id,
                        "required_capabilities": contract.required_capabilities,
                        "missing_capabilities": missing_caps,
                    },
                )
                obs = Observation(
                    task_id=task.task_id,
                    task_type="subworkflow",
                    status="FAILED",
                    semantic_summary=rejection_summary,
                )
                context.recent_observations.append(obs)
                new_obs.append(obs)
                continue

            # -----------------------------------------------------------------
            # Delegation governance evaluation (depth + budget policies)
            # -----------------------------------------------------------------
            if self._governance is not None:
                # Temporarily attach delegation context attributes so policies can
                # inspect coordinator depth and pending contract without circular deps.
                context._coordinator_ref = self._coordinator  # type: ignore[attr-defined]
                context._pending_contract = contract  # type: ignore[attr-defined]
                context._tool_registry_ref = self._tool_registry  # type: ignore[attr-defined]
                context._prompt_registry_ref = self._prompt_capability_registry  # type: ignore[attr-defined]

                from freya.dag.models import DAG as _DAG
                gov_result = self._governance.evaluate(context, _DAG(tasks=[]))

                # Clean up temp attributes
                for _attr in ("_coordinator_ref", "_pending_contract",
                               "_tool_registry_ref", "_prompt_registry_ref"):
                    try:
                        delattr(context, _attr)
                    except AttributeError:
                        pass

                if gov_result.decision == InterventionDecision.REJECT:
                    rejection_summary = (
                        f"delegation rejected: {gov_result.reason} for task {task.task_id}"
                    )
                    context.child_workflow_summaries.append(rejection_summary)
                    context.failed_tasks.append(task.task_id)
                    context.task_results[task.task_id] = {
                        "status": "FAILED",
                        "output": None,
                        "error": rejection_summary,
                    }
                    planner_trace.events.append(PlannerEvent(
                        event_type="delegation_contract_rejected",
                        iteration=iteration,
                        payload={
                            "contract_id": contract.contract_id,
                            "task_id": task.task_id,
                            "reason": gov_result.reason,
                            "triggered_policies": gov_result.triggered_policies,
                        },
                    ))
                    await self._emit(
                        EventType.DELEGATION_CONTRACT_REJECTED, session_id,
                        iteration=iteration,
                        workflow_state=WorkflowState.RUNNING,
                        payload={
                            "contract_id": contract.contract_id,
                            "reason": gov_result.reason,
                            "triggered_policies": gov_result.triggered_policies,
                        },
                    )
                    obs = Observation(
                        task_id=task.task_id,
                        task_type="subworkflow",
                        status="FAILED",
                        semantic_summary=rejection_summary,
                    )
                    context.recent_observations.append(obs)
                    new_obs.append(obs)
                    continue

            # -----------------------------------------------------------------
            # Contract validated — register and spawn
            # -----------------------------------------------------------------
            planner_trace.events.append(PlannerEvent(
                event_type="delegation_contract_validated",
                iteration=iteration,
                payload={
                    "contract_id": contract.contract_id,
                    "task_id": task.task_id,
                    "required_capabilities": contract.required_capabilities,
                },
            ))
            await self._emit(
                EventType.DELEGATION_CONTRACT_VALIDATED, session_id,
                iteration=iteration,
                workflow_state=WorkflowState.RUNNING,
                payload={
                    "contract_id": contract.contract_id,
                    "required_capabilities": contract.required_capabilities,
                },
            )

            if self._coordinator is not None:
                rel = self._coordinator.spawn_subworkflow(
                    parent_session_id=session_id,
                    child_session_id=child_session_id,
                    relationship_type=RelationshipType.SPAWNED_SUBWORKFLOW,
                )
                self._coordinator.register_contract(contract)
                planner_trace.events.append(PlannerEvent(
                    event_type="workflow_relationship_created",
                    iteration=iteration,
                    payload={
                        "parent_session_id": session_id,
                        "child_session_id": child_session_id,
                        "relationship_type": rel.relationship_type,
                        "task_id": task.task_id,
                        "contract_id": contract.contract_id,
                    },
                ))
                await self._emit(
                    EventType.WORKFLOW_RELATIONSHIP_CREATED, session_id,
                    iteration=iteration,
                    payload={
                        "parent_session_id": session_id,
                        "child_session_id": child_session_id,
                        "relationship_type": rel.relationship_type,
                        "contract_id": contract.contract_id,
                    },
                )

            # Emit spawned event
            planner_trace.events.append(PlannerEvent(
                event_type="subworkflow_spawned",
                iteration=iteration,
                payload={
                    "parent_session_id": session_id,
                    "child_session_id": child_session_id,
                    "task_id": task.task_id,
                    "goal": child_goal,
                    "planning_mode": planning_mode_str,
                    "contract_id": contract.contract_id,
                },
            ))
            await self._emit(
                EventType.SUBWORKFLOW_SPAWNED, session_id,
                iteration=iteration,
                workflow_state=WorkflowState.RUNNING,
                payload={
                    "parent_session_id": session_id,
                    "child_session_id": child_session_id,
                    "relationship_type": RelationshipType.SPAWNED_SUBWORKFLOW,
                    "task_id": task.task_id,
                    "contract_id": contract.contract_id,
                },
            )

            # Determine child planning mode
            try:
                child_mode = PlanningMode(planning_mode_str)
            except ValueError:
                child_mode = self._planning_mode

            # Determine iteration cap from contract
            child_max_iterations = (
                contract.max_iterations
                if contract.max_iterations is not None
                else MAX_ITERATIONS
            )

            # Spawn child runner — inherits governance, event bus, persistence store
            child_runner = IterativePlannerRunner(
                planner=self._planner,
                dag_runner=self._dag_runner,
                tool_registry=self._tool_registry,
                memory=self._memory,
                planning_mode=child_mode,
                prompt_capability_registry=self._prompt_capability_registry,
                governance_engine=self._governance,
                approval_store=self._approval_store,
                persistent_store=self._persistent_store,
                event_bus=self._event_bus,
                coordinator=self._coordinator,
            )

            # Execute child workflow under contract budget
            child_result = await child_runner.run(
                child_goal,
                session_id=child_session_id,
                max_iterations=child_max_iterations,
            )

            # -----------------------------------------------------------------
            # Build summary observation
            # -----------------------------------------------------------------
            if child_result.workflow_state == WorkflowState.COMPLETED:
                summary = f"subworkflow {task.task_id} succeeded under contract"
                context.task_results[task.task_id] = {
                    "status": "SUCCESS",
                    "output": {
                        "child_session_id": child_session_id,
                        "contract_id": contract.contract_id,
                        "completed_tasks": list(child_result.final_context.completed_tasks),
                    },
                    "error": None,
                }
                context.completed_tasks.append(task.task_id)
                planner_trace.events.append(PlannerEvent(
                    event_type="subworkflow_completed",
                    iteration=iteration,
                    payload={
                        "parent_session_id": session_id,
                        "child_session_id": child_session_id,
                        "task_id": task.task_id,
                        "contract_id": contract.contract_id,
                        "completed_tasks": list(child_result.final_context.completed_tasks),
                    },
                ))
                await self._emit(
                    EventType.SUBWORKFLOW_COMPLETED, session_id,
                    iteration=iteration,
                    workflow_state=WorkflowState.RUNNING,
                    payload={
                        "parent_session_id": session_id,
                        "child_session_id": child_session_id,
                        "relationship_type": RelationshipType.SPAWNED_SUBWORKFLOW,
                        "contract_id": contract.contract_id,
                    },
                )
            elif child_result.workflow_state == WorkflowState.PAUSED_FOR_APPROVAL:
                summary = f"subworkflow {task.task_id} paused for approval (governed independently)"
                context.task_results[task.task_id] = {
                    "status": "PAUSED",
                    "output": {
                        "child_session_id": child_session_id,
                        "contract_id": contract.contract_id,
                        "approval_request_id": child_result.approval_request_id,
                    },
                    "error": None,
                }
                context.completed_tasks.append(task.task_id)
                planner_trace.events.append(PlannerEvent(
                    event_type="subworkflow_completed",
                    iteration=iteration,
                    payload={
                        "parent_session_id": session_id,
                        "child_session_id": child_session_id,
                        "task_id": task.task_id,
                        "contract_id": contract.contract_id,
                        "child_state": "paused_for_approval",
                    },
                ))
            else:
                failure_state = child_result.workflow_state.value
                summary = f"subworkflow {task.task_id} failed due to {failure_state}"
                context.task_results[task.task_id] = {
                    "status": "FAILED",
                    "output": None,
                    "error": f"child workflow ended with state {failure_state}",
                }
                context.failed_tasks.append(task.task_id)
                planner_trace.events.append(PlannerEvent(
                    event_type="subworkflow_failed",
                    iteration=iteration,
                    payload={
                        "parent_session_id": session_id,
                        "child_session_id": child_session_id,
                        "task_id": task.task_id,
                        "contract_id": contract.contract_id,
                        "child_state": failure_state,
                    },
                ))
                await self._emit(
                    EventType.SUBWORKFLOW_FAILED, session_id,
                    iteration=iteration,
                    workflow_state=WorkflowState.RUNNING,
                    payload={
                        "parent_session_id": session_id,
                        "child_session_id": child_session_id,
                        "relationship_type": RelationshipType.SPAWNED_SUBWORKFLOW,
                        "contract_id": contract.contract_id,
                        "child_state": failure_state,
                    },
                )

            context.child_workflow_summaries.append(summary)

            child_status = (
                "SUCCESS"
                if child_result.workflow_state in (
                    WorkflowState.COMPLETED, WorkflowState.PAUSED_FOR_APPROVAL
                )
                else "FAILED"
            )
            obs = Observation(
                task_id=task.task_id,
                task_type="subworkflow",
                status=child_status,
                semantic_summary=summary,
            )
            context.recent_observations.append(obs)
            new_obs.append(obs)

        return new_obs

    async def run(
        self,
        goal: str,
        session_id: str | None = None,
        max_iterations: int = MAX_ITERATIONS,
    ) -> PlannerResult:
        session_id = session_id or str(uuid.uuid4())
        recovery_counts: dict[str, int] = {}  # per-task runtime recovery count
        runtime_signals = RuntimeSignals()
        strategy_history: list[dict] = []

        # Export tool capabilities once for the entire run.
        capabilities = self._tool_registry.export_capabilities()

        # Load prompt capabilities in COGNITIVE mode.
        prompt_caps: list = []
        if (
            self._planning_mode == PlanningMode.COGNITIVE
            and self._prompt_capability_registry is not None
        ):
            prompt_caps = self._prompt_capability_registry.list_capabilities(
                mode=PlanningMode.COGNITIVE
            )

        context = PlanningContext(
            session_id=session_id,
            goal=goal,
            planning_mode=self._planning_mode,
            available_tools=capabilities,
            available_prompt_capabilities=prompt_caps,
        )
        planner_trace = PlannerTrace(session_id=session_id, goal=goal)

        # Emit mode-selected event.
        planner_trace.events.append(
            PlannerEvent(
                event_type="planner_mode_selected",
                iteration=0,
                payload={"mode": self._planning_mode.value},
            )
        )
        await self._emit(EventType.PLANNER_MODE_SELECTED, session_id, iteration=0,
                         payload={"mode": self._planning_mode.value})

        # Emit tool capabilities-loaded event.
        planner_trace.events.append(
            PlannerEvent(
                event_type="planner_capabilities_loaded",
                iteration=0,
                payload={
                    "tool_count": len(capabilities),
                    "tool_names": [c.name for c in capabilities],
                },
            )
        )

        # Emit prompt capabilities-loaded event.
        planner_trace.events.append(
            PlannerEvent(
                event_type="planner_prompt_capabilities_loaded",
                iteration=0,
                payload={
                    "mode": self._planning_mode.value,
                    "capability_names": [c.name for c in prompt_caps],
                },
            )
        )

        total_tasks = 0
        termination_reason: str | None = None

        for iteration in range(max_iterations):
            context.iteration_count = iteration

            # Snapshot memory so the planner can read previously stored values.
            context.memory_snapshot = {
                key: self._memory.get(session_id, key)
                for key in self._memory.list_keys(session_id)
            }

            logger.info("Planner iteration %d  goal=%r", iteration, goal)

            # -----------------------------------------------------------------
            # Strategy selection
            # -----------------------------------------------------------------
            if self._strategy_engine is not None:
                strategy_decision = self._strategy_engine.select_strategy(
                    context, None, runtime_signals
                )
                strategy_history.append({
                    "iteration": iteration,
                    **strategy_decision.model_dump(mode="json"),
                })

                # Record economics cost for this strategy
                if self._economics is not None:
                    self._economics.record_strategy(strategy_decision.strategy)
                    if not self._economics.within_budget():
                        exceeded = self._economics.exceeded_fields()
                        planner_trace.events.append(PlannerEvent(
                            event_type="workflow_budget_exceeded",
                            iteration=iteration,
                            payload={
                                "exceeded_fields": exceeded,
                                "accumulated_cost": self._economics.current_cost().model_dump(),
                            },
                        ))
                        await self._emit(
                            EventType.WORKFLOW_BUDGET_EXCEEDED, session_id,
                            iteration=iteration, workflow_state=WorkflowState.RUNNING,
                            payload={"exceeded_fields": exceeded},
                        )

                planner_trace.events.append(PlannerEvent(
                    event_type="execution_strategy_selected",
                    iteration=iteration,
                    payload={
                        "strategy": strategy_decision.strategy.value,
                        "reason": strategy_decision.reason,
                        "confidence": strategy_decision.confidence,
                        "triggered_by": strategy_decision.triggered_by,
                    },
                ))
                await self._emit(
                    EventType.EXECUTION_STRATEGY_SELECTED, session_id,
                    iteration=iteration, workflow_state=WorkflowState.RUNNING,
                    payload={
                        "strategy": strategy_decision.strategy.value,
                        "reason": strategy_decision.reason,
                        "triggered_by": strategy_decision.triggered_by,
                    },
                )

                # Act on terminate decision immediately
                if strategy_decision.strategy == ExecutionStrategy.TERMINATE:
                    planner_trace.events.append(PlannerEvent(
                        event_type="execution_strategy_terminated",
                        iteration=iteration,
                        payload={
                            "reason": strategy_decision.reason,
                            "triggered_by": strategy_decision.triggered_by,
                        },
                    ))
                    await self._emit(
                        EventType.EXECUTION_STRATEGY_TERMINATED, session_id,
                        iteration=iteration, workflow_state=WorkflowState.RUNNING,
                        payload={"reason": strategy_decision.reason},
                    )
                    planner_trace.status = "FAILED"
                    planner_trace.termination_reason = "strategy_terminated"
                    planner_trace.end_time = time.time()
                    planner_trace.iterations_completed = iteration
                    return PlannerResult(session_id, goal, context, planner_trace,
                                         workflow_state=WorkflowState.FAILED)

            await self._emit(EventType.PLANNER_ITERATION_STARTED, session_id,
                             iteration=iteration, workflow_state=WorkflowState.RUNNING,
                             payload={"goal": goal})

            # Build compressed context and emit trace event.
            compressed = build_planner_context(context)
            planner_trace.events.append(
                PlannerEvent(
                    event_type="planner_context_built",
                    iteration=iteration,
                    payload={
                        "observation_summaries": compressed["recent_observation_summaries"],
                        "memory_summary": compressed["memory_summary"],
                    },
                )
            )

            # -----------------------------------------------------------------
            # Generate next DAG fragment → validate → repair (bounded)
            # -----------------------------------------------------------------
            dag: DAG | None = None
            broken_candidate: DAG | None = None
            repair_count = 0

            # Step 1: generate initial candidate
            try:
                candidate = await self._planner.plan_next(context)
            except Exception as exc:
                logger.warning("planner.plan_next raised: %s", exc)
                _add_repair_obs(context, "plan_next", str(exc))
                termination_reason = "planner_plan_next_failed"
                planner_trace.events.append(PlannerEvent(
                    event_type="planner_terminated",
                    iteration=iteration,
                    payload={"reason": termination_reason, "error": str(exc)},
                ))
                planner_trace.status = "FAILED"
                planner_trace.termination_reason = termination_reason
                planner_trace.end_time = time.time()
                planner_trace.iterations_completed = iteration
                return PlannerResult(session_id, goal, context, planner_trace,
                                     workflow_state=WorkflowState.FAILED)

            # Empty DAG → planner signals completion
            if not candidate.tasks:
                dag = candidate
            else:
                # Step 2: validate
                vr = validate_dag_fragment(candidate, self._tool_registry, context)
                if vr.valid:
                    dag = candidate
                else:
                    issues_text = vr.as_text()
                    logger.warning("DAG validation failed: %s", issues_text)
                    runtime_signals = RuntimeSignals(
                        **{**runtime_signals.model_dump(),
                           "validation_failures": runtime_signals.validation_failures + 1}
                    )
                    planner_trace.events.append(PlannerEvent(
                        event_type="planner_validation_failed",
                        iteration=iteration,
                        payload={"issues": [i.model_dump() for i in vr.issues], "attempt": 0},
                    ))

                    # Step 3: one repair attempt
                    if repair_count < MAX_REPAIR_ATTEMPTS:
                        repair_count += 1
                        planner_trace.events.append(PlannerEvent(
                            event_type="planner_repair_attempted",
                            iteration=iteration,
                            payload={"repair_attempt": repair_count, "issues": issues_text},
                        ))
                        try:
                            repaired = await self._planner.repair_dag(
                                context, candidate, issues_text
                            )
                        except Exception as repair_exc:
                            logger.warning("repair_dag raised: %s", repair_exc)
                            repaired = None

                        if repaired is not None and repaired.tasks:
                            rvr = validate_dag_fragment(repaired, self._tool_registry, context)
                            if rvr.valid:
                                planner_trace.events.append(PlannerEvent(
                                    event_type="planner_repair_succeeded",
                                    iteration=iteration,
                                    payload={"repair_attempt": repair_count},
                                ))
                                dag = repaired
                            else:
                                planner_trace.events.append(PlannerEvent(
                                    event_type="planner_repair_failed",
                                    iteration=iteration,
                                    payload={"issues": [i.model_dump() for i in rvr.issues]},
                                ))
                                _add_repair_obs(
                                    context, candidate.tasks[0].task_id,
                                    f"planner generated invalid DAG: {rvr.as_text()}",
                                    repair_attempted=True,
                                )
                        else:
                            planner_trace.events.append(PlannerEvent(
                                event_type="planner_repair_failed",
                                iteration=iteration,
                                payload={"error": "repair_dag returned empty or unparseable result"},
                            ))
                            _add_repair_obs(
                                context, candidate.tasks[0].task_id,
                                f"planner generated invalid DAG: {issues_text}",
                                repair_attempted=True,
                            )

                    if dag is None:
                        termination_reason = "dag_validation_failed_after_repair"
                        planner_trace.events.append(PlannerEvent(
                            event_type="planner_terminated",
                            iteration=iteration,
                            payload={"reason": termination_reason, "issues": issues_text},
                        ))
                        planner_trace.status = "FAILED"
                        planner_trace.termination_reason = termination_reason
                        planner_trace.end_time = time.time()
                        planner_trace.iterations_completed = iteration
                        return PlannerResult(session_id, goal, context, planner_trace,
                                             workflow_state=WorkflowState.FAILED)

            # -----------------------------------------------------------------
            # Termination: planner signalled completion via empty DAG
            # -----------------------------------------------------------------
            if dag is not None and not dag.tasks:
                termination_reason = "planner_returned_empty_dag"
                planner_trace.events.append(
                    PlannerEvent(
                        event_type="planner_terminated",
                        iteration=iteration,
                        payload={"reason": termination_reason},
                    )
                )
                break

            if dag is None:
                # Should not happen — handled above, but guard against it
                termination_reason = "internal_planner_error"
                planner_trace.status = "FAILED"
                break

            # -----------------------------------------------------------------
            # Safety: cap total tasks across all iterations
            # -----------------------------------------------------------------
            total_tasks += len(dag.tasks)
            if total_tasks > MAX_TOTAL_TASKS:
                termination_reason = "max_total_tasks_exceeded"
                planner_trace.events.append(
                    PlannerEvent(
                        event_type="planner_terminated",
                        iteration=iteration,
                        payload={"reason": termination_reason, "total_tasks": total_tasks},
                    )
                )
                planner_trace.status = "FAILED"
                planner_trace.termination_reason = termination_reason
                planner_trace.end_time = time.time()
                planner_trace.iterations_completed = iteration
                return PlannerResult(session_id, goal, context, planner_trace,
                                     workflow_state=WorkflowState.FAILED)

            # -----------------------------------------------------------------
            # Governance evaluation — enforce pause when REQUIRE_APPROVAL
            # -----------------------------------------------------------------
            if self._governance is not None:
                gov_decision = self._governance.evaluate(context, dag)

                # Emit per-policy trigger events
                for policy_name in gov_decision.triggered_policies:
                    planner_trace.events.append(PlannerEvent(
                        event_type="governance_policy_triggered",
                        iteration=iteration,
                        payload={"policy": policy_name},
                    ))

                # Emit aggregated governance decision event
                planner_trace.events.append(PlannerEvent(
                    event_type="governance_evaluated",
                    iteration=iteration,
                    payload={
                        "decision": gov_decision.decision.value,
                        "reason": gov_decision.reason,
                        "risk_level": gov_decision.risk_level,
                        "triggered_policies": gov_decision.triggered_policies,
                    },
                ))
                await self._emit(EventType.GOVERNANCE_EVALUATED, session_id,
                                 iteration=iteration,
                                 workflow_state=WorkflowState.RUNNING,
                                 payload={
                                     "decision": gov_decision.decision.value,
                                     "reason": gov_decision.reason,
                                     "risk_level": gov_decision.risk_level,
                                     "triggered_policies": gov_decision.triggered_policies,
                                 })

                if gov_decision.decision == InterventionDecision.REJECT:
                    # Hard reject — terminate immediately.
                    runtime_signals = RuntimeSignals(
                        **{**runtime_signals.model_dump(),
                           "governance_blocks": runtime_signals.governance_blocks + 1}
                    )
                    _add_governance_obs(
                        context,
                        dag.tasks[0].task_id if dag.tasks else "unknown",
                        "workflow rejected by governance",
                    )
                    planner_trace.events.append(PlannerEvent(
                        event_type="workflow_rejected_by_governance",
                        iteration=iteration,
                        payload={"reason": gov_decision.reason},
                    ))
                    planner_trace.events.append(PlannerEvent(
                        event_type="planner_terminated",
                        iteration=iteration,
                        payload={"reason": "governance_rejected"},
                    ))
                    planner_trace.status = "FAILED"
                    planner_trace.termination_reason = "governance_rejected"
                    planner_trace.end_time = time.time()
                    planner_trace.iterations_completed = iteration
                    return PlannerResult(
                        session_id, goal, context, planner_trace,
                        workflow_state=WorkflowState.REJECTED,
                    )

                if gov_decision.decision == InterventionDecision.REQUIRE_APPROVAL:
                    # Pause — create an approval request and stop execution.
                    runtime_signals = RuntimeSignals(
                        **{**runtime_signals.model_dump(),
                           "pending_approvals": runtime_signals.pending_approvals + 1}
                    )
                    obs_summaries = [
                        o.as_summary() for o in context.recent_observations
                        if o.semantic_summary
                    ]
                    approval_req = ApprovalRequest(
                        session_id=session_id,
                        iteration=iteration,
                        proposed_dag=dag.model_dump(),
                        governance_reason=gov_decision.reason,
                        risk_level=gov_decision.risk_level,
                        triggered_policies=gov_decision.triggered_policies,
                        observation_summaries=obs_summaries,
                    )
                    if self._approval_store is not None:
                        self._approval_store.create(approval_req)

                    _add_governance_obs(
                        context,
                        dag.tasks[0].task_id if dag.tasks else "unknown",
                        "workflow paused awaiting approval due to governance policy",
                    )
                    planner_trace.events.append(PlannerEvent(
                        event_type="workflow_paused_for_approval",
                        iteration=iteration,
                        payload={
                            "request_id": approval_req.request_id,
                            "risk_level": gov_decision.risk_level,
                            "triggered_policies": gov_decision.triggered_policies,
                        },
                    ))
                    # Persist snapshot + approval to durable store if configured.
                    if self._persistent_store is not None:
                        # Collect active delegation contracts from coordinator
                        _active_contracts: list[dict] = []
                        if self._coordinator is not None:
                            for _c in self._coordinator.all_contracts():
                                try:
                                    _active_contracts.append(_c.model_dump(mode="json"))  # type: ignore[attr-defined]
                                except Exception:
                                    pass
                        snapshot = WorkflowSnapshot(
                            session_id=session_id,
                            workflow_state=WorkflowState.PAUSED_FOR_APPROVAL,
                            iteration=iteration,
                            planning_mode=self._planning_mode.value,
                            goal=goal,
                            completed_tasks=list(context.completed_tasks),
                            failed_tasks=list(context.failed_tasks),
                            task_results=dict(context.task_results),
                            recent_observations=[
                                obs.to_dict() for obs in context.recent_observations
                            ],
                            memory_state={
                                key: self._memory.get(session_id, key)
                                for key in self._memory.list_keys(session_id)
                            },
                            paused_dag_fragment=dag.model_dump(),
                            approval_request_id=approval_req.request_id,
                            lease_owner=self.runner_id,
                            active_contracts=_active_contracts,
                            current_strategy=(
                                strategy_history[-1]["strategy"]
                                if strategy_history else None
                            ),
                            strategy_history=list(strategy_history),
                            accumulated_cost=(
                                self._economics.current_cost().model_dump()
                                if self._economics is not None else {}
                            ),
                            strategy_cost_history=(
                                self._economics.strategy_history()
                                if self._economics is not None else []
                            ),
                            budget=(
                                self._economics._budget.model_dump()
                                if self._economics is not None else {}
                            ),
                            workflow_priority=(
                                self._economics._priority.value
                                if self._economics is not None else "normal"
                            ),
                        )
                        # New snapshots always have expected_version=0 (initial write).
                        snapshot_path = self._persistent_store.save_snapshot(
                            snapshot, expected_version=0
                        )
                        self._persistent_store.save_approval(approval_req)
                        planner_trace.events.append(PlannerEvent(
                            event_type="workflow_snapshot_persisted",
                            iteration=iteration,
                            payload={
                                "session_id": session_id,
                                "snapshot_path": str(snapshot_path),
                                "version": snapshot.version + 1,  # post-save version
                                "runner_id": self.runner_id,
                            },
                        ))
                        planner_trace.events.append(PlannerEvent(
                            event_type="workflow_lease_acquired",
                            iteration=iteration,
                            payload={
                                "session_id": session_id,
                                "runner_id": self.runner_id,
                            },
                        ))
                        await self._emit(EventType.WORKFLOW_SNAPSHOT_PERSISTED, session_id,
                                         iteration=iteration,
                                         workflow_state=WorkflowState.PAUSED_FOR_APPROVAL,
                                         payload={
                                             "snapshot_path": str(snapshot_path),
                                             "version": snapshot.version + 1,
                                             "runner_id": self.runner_id,
                                         })
                        await self._emit(EventType.WORKFLOW_LEASE_ACQUIRED, session_id,
                                         iteration=iteration,
                                         workflow_state=WorkflowState.PAUSED_FOR_APPROVAL,
                                         payload={"runner_id": self.runner_id})

                    # Store paused state on the runner for resume.
                    self._paused_dag = dag
                    self._paused_context = context
                    self._paused_trace = planner_trace
                    self._paused_iteration = iteration
                    self._paused_session_id = session_id
                    self._paused_goal = goal
                    self._paused_recovery_counts = recovery_counts
                    self._paused_total_tasks = total_tasks
                    self._paused_max_iterations = max_iterations

                    planner_trace.termination_reason = "paused_for_approval"
                    planner_trace.end_time = time.time()
                    planner_trace.iterations_completed = iteration
                    await self._emit(
                        EventType.WORKFLOW_PAUSED_FOR_APPROVAL, session_id,
                        iteration=iteration,
                        workflow_state=WorkflowState.PAUSED_FOR_APPROVAL,
                        payload={
                            "request_id": approval_req.request_id,
                            "risk_level": gov_decision.risk_level,
                            "triggered_policies": gov_decision.triggered_policies,
                            "runner_id": self.runner_id,
                        },
                    )
                    return PlannerResult(
                        session_id, goal, context, planner_trace,
                        workflow_state=WorkflowState.PAUSED_FOR_APPROVAL,
                        approval_request_id=approval_req.request_id,
                    )

                # APPROVE — record advisory observation if policies were triggered.
                if gov_decision.triggered_policies:
                    _add_governance_obs(
                        context,
                        dag.tasks[0].task_id if dag.tasks else "unknown",
                        f"governance flagged DAG for {gov_decision.decision.value}: "
                        f"{gov_decision.reason}",
                    )

            # -----------------------------------------------------------------
            # Execute DAG fragment (handle subworkflow tasks inline)
            # -----------------------------------------------------------------
            sw_tasks = [t for t in dag.tasks if t.type == "subworkflow"]
            regular_tasks = [t for t in dag.tasks if t.type != "subworkflow"]

            # Pre-compute all task IDs for the planner_iteration event
            planner_trace.events.append(
                PlannerEvent(
                    event_type="planner_iteration",
                    iteration=iteration,
                    payload={
                        "tasks": [t.task_id for t in dag.tasks],
                        "task_count": len(dag.tasks),
                    },
                )
            )

            # Run subworkflow tasks inline first (child runners, summarized obs)
            if sw_tasks:
                sw_obs = await self._run_subworkflow_tasks(
                    sw_tasks, context, planner_trace, iteration, session_id, goal
                )
            else:
                sw_obs = []

            # If no regular tool/llm tasks remain, continue to next iteration
            if not regular_tasks:
                planner_trace.events.append(PlannerEvent(
                    event_type="planner_observations_updated",
                    iteration=iteration,
                    payload={
                        "observation_count": len(context.recent_observations),
                        "new_observations": [o.as_summary() for o in sw_obs],
                    },
                ))
                await self._emit(EventType.PLANNER_ITERATION_COMPLETED, session_id,
                                 iteration=iteration, workflow_state=WorkflowState.RUNNING,
                                 payload={
                                     "completed_tasks": list(context.completed_tasks),
                                     "new_observations": [o.as_summary() for o in sw_obs],
                                 })
                continue

            # Execute remaining tool/llm tasks via DAGRunner
            dag_for_runner = DAG(tasks=regular_tasks) if sw_tasks else dag
            dag_result = await self._dag_runner.run(
                dag_for_runner,
                memory=self._memory,
                session_id=session_id,
            )

            # -----------------------------------------------------------------
            # Update context from execution results + collect observations
            # -----------------------------------------------------------------
            new_obs: list[Observation] = list(sw_obs)
            for task_id, task_result in dag_result.results.items():
                context.task_results[task_id] = {
                    "status": task_result.status,
                    "output": task_result.output,
                    "error": task_result.error,
                }
                if task_result.status == "SUCCESS":
                    context.completed_tasks.append(task_id)
                else:
                    context.failed_tasks.append(task_id)

                # Build observation (no raw traces)
                task_type = "unknown"
                for t in dag_for_runner.tasks:
                    if t.task_id == task_id:
                        task_type = t.type
                        break

                obs = Observation.from_task_result(
                    task_id=task_id,
                    task_type=task_type,
                    status=task_result.status,
                    output=task_result.output,
                    error=_sanitize_error(task_result.error),
                )
                context.recent_observations.append(obs)
                new_obs.append(obs)

            # Emit observations-updated event.
            planner_trace.events.append(
                PlannerEvent(
                    event_type="planner_observations_updated",
                    iteration=iteration,
                    payload={
                        "observation_count": len(context.recent_observations),
                        "new_observations": [o.as_summary() for o in new_obs],
                    },
                )
            )
            await self._emit(EventType.PLANNER_ITERATION_COMPLETED, session_id,
                             iteration=iteration, workflow_state=WorkflowState.RUNNING,
                             payload={
                                 "completed_tasks": list(context.completed_tasks),
                                 "new_observations": [o.as_summary() for o in new_obs],
                             })

            if dag_result.dag_trace:
                context.trace_summary[f"iteration_{iteration}"] = {
                    "status": dag_result.dag_trace.status,
                    "task_count": len(dag_result.dag_trace.task_traces),
                }

            # -----------------------------------------------------------------
            # Runtime failure recovery
            # -----------------------------------------------------------------
            if dag_result.status == "FAILED":
                runtime_signals = RuntimeSignals(
                    **{**runtime_signals.model_dump(),
                       "runtime_failures": runtime_signals.runtime_failures + 1}
                )
                recovery_outcome = await self._handle_runtime_failures(
                    dag=dag_for_runner,
                    dag_result=dag_result,
                    context=context,
                    planner_trace=planner_trace,
                    iteration=iteration,
                    recovery_counts=recovery_counts,
                    session_id=session_id,
                    goal=goal,
                )
                if recovery_outcome == "recover":
                    runtime_signals = RuntimeSignals(
                        **{**runtime_signals.model_dump(),
                           "recovery_attempts": runtime_signals.recovery_attempts + 1}
                    )
                if recovery_outcome == "terminate":
                    return PlannerResult(session_id, goal, context, planner_trace,
                                         workflow_state=WorkflowState.FAILED)
                # "recovered" or "continue" → fall through to next iteration

        else:
            # for-loop exhausted without a break → max iterations reached
            termination_reason = "max_iterations_reached"
            planner_trace.status = "MAX_ITERATIONS_REACHED"
            planner_trace.events.append(
                PlannerEvent(
                    event_type="planner_terminated",
                    iteration=max_iterations - 1,
                    payload={"reason": termination_reason, "max_iterations": max_iterations},
                )
            )

        planner_trace.termination_reason = termination_reason
        planner_trace.end_time = time.time()
        planner_trace.iterations_completed = context.iteration_count + 1
        await self._emit(EventType.WORKFLOW_COMPLETED, session_id,
                         iteration=context.iteration_count,
                         workflow_state=WorkflowState.COMPLETED,
                         payload={
                             "goal": goal,
                             "completed_tasks": list(context.completed_tasks),
                             "termination_reason": termination_reason,
                         })
        return PlannerResult(session_id, goal, context, planner_trace,
                             workflow_state=WorkflowState.COMPLETED)

    # ------------------------------------------------------------------
    # Approval resume
    # ------------------------------------------------------------------

    def restore_workflow(self, session_id: str) -> WorkflowState:
        """Load a persisted WorkflowSnapshot and reconstruct in-memory state.

        Acquires an execution lease for this runner before restoring.  If
        another runner holds a valid (non-expired) lease a
        :class:`~freya.governance.errors.WorkflowLeaseError` is raised.

        Validates that the snapshot is in a resumable state.  A snapshot
        whose ``workflow_state`` is not ``PAUSED_FOR_APPROVAL`` raises a
        :class:`~freya.governance.errors.WorkflowAlreadyResumedError`.

        Returns the restored :class:`WorkflowState`.
        """
        if self._persistent_store is None:
            raise RuntimeError("No PersistentWorkflowStore configured on this runner.")
        snapshot = self._persistent_store.load_snapshot(session_id)
        if snapshot is None:
            raise RuntimeError(f"No snapshot found for session '{session_id}'.")

        # Validate that the snapshot is in a resumable state.
        if snapshot.workflow_state not in (
            WorkflowState.PAUSED_FOR_APPROVAL,
        ):
            raise WorkflowAlreadyResumedError(session_id, snapshot.workflow_state.value)

        # Validate approval linkage.
        if snapshot.approval_request_id is None:
            raise RuntimeError(
                f"Snapshot for session '{session_id}' is in "
                f"{snapshot.workflow_state.value!r} but has no approval_request_id."
            )

        # Acquire lease — raises WorkflowLeaseError if held by another runner.
        leased = self._persistent_store.acquire_lease(
            session_id, self.runner_id, ttl_seconds=60
        )

        # Restore memory from the snapshot.
        for key, value in snapshot.memory_state.items():
            self._memory.set(session_id, key, value)

        # Re-export live capabilities (runtime objects — not persisted).
        caps = self._tool_registry.export_capabilities()
        prompt_caps: list = []
        if (
            PlanningMode(snapshot.planning_mode) == PlanningMode.COGNITIVE
            and self._prompt_capability_registry is not None
        ):
            prompt_caps = self._prompt_capability_registry.list_capabilities(
                mode=PlanningMode.COGNITIVE
            )

        # Reconstruct PlanningContext from serialized execution state.
        context = PlanningContext(
            session_id=session_id,
            goal=snapshot.goal,
            planning_mode=PlanningMode(snapshot.planning_mode),
            completed_tasks=list(snapshot.completed_tasks),
            failed_tasks=list(snapshot.failed_tasks),
            task_results=dict(snapshot.task_results),
            recent_observations=[
                Observation.from_dict(o) for o in snapshot.recent_observations
            ],
            available_tools=caps,
            available_prompt_capabilities=prompt_caps,
            iteration_count=snapshot.iteration,
            memory_snapshot={
                key: self._memory.get(session_id, key)
                for key in self._memory.list_keys(session_id)
            },
        )

        # Create a fresh trace for the restored execution segment.
        planner_trace = PlannerTrace(session_id=session_id, goal=snapshot.goal)
        planner_trace.events.append(PlannerEvent(
            event_type="workflow_snapshot_restored",
            iteration=snapshot.iteration,
            payload={
                "session_id": session_id,
                "snapshot_id": snapshot.snapshot_id,
                "version": leased.version,
                "runner_id": self.runner_id,
            },
        ))
        planner_trace.events.append(PlannerEvent(
            event_type="workflow_state_restored",
            iteration=snapshot.iteration,
            payload={
                "workflow_state": snapshot.workflow_state.value,
                "completed_tasks": snapshot.completed_tasks,
                "observation_count": len(snapshot.recent_observations),
            },
        ))
        planner_trace.events.append(PlannerEvent(
            event_type="workflow_lease_acquired",
            iteration=snapshot.iteration,
            payload={
                "session_id": session_id,
                "runner_id": self.runner_id,
                "lease_expires_at": (
                    leased.lease_expires_at.isoformat()
                    if leased.lease_expires_at
                    else None
                ),
            },
        ))

        # Restore paused DAG and all runner state needed for resume.
        if snapshot.paused_dag_fragment is not None:
            from freya.dag.models import DAG as _DAG
            self._paused_dag = _DAG.model_validate(snapshot.paused_dag_fragment)
        self._paused_context = context
        self._paused_trace = planner_trace
        self._paused_iteration = snapshot.iteration
        self._paused_session_id = session_id
        self._paused_goal = snapshot.goal
        self._paused_recovery_counts: dict[str, int] = {}
        self._paused_total_tasks = len(snapshot.completed_tasks)
        self._paused_max_iterations = MAX_ITERATIONS
        # Store snapshot version so resume can pass expected_version on writes.
        self._paused_snapshot_version = leased.version

        # Emit bus events (fire-and-forget; restore_workflow is synchronous so
        # we schedule these via a best-effort approach — callers who need to
        # react immediately should await publish themselves).
        import asyncio as _asyncio
        loop = None
        try:
            loop = _asyncio.get_running_loop()
        except RuntimeError:
            pass
        if loop is not None:
            loop.create_task(self._emit(
                EventType.WORKFLOW_SNAPSHOT_RESTORED, session_id,
                iteration=snapshot.iteration,
                workflow_state=snapshot.workflow_state,
                payload={"snapshot_id": snapshot.snapshot_id, "version": leased.version,
                         "runner_id": self.runner_id},
            ))
            loop.create_task(self._emit(
                EventType.WORKFLOW_LEASE_ACQUIRED, session_id,
                iteration=snapshot.iteration,
                workflow_state=snapshot.workflow_state,
                payload={"runner_id": self.runner_id,
                         "lease_expires_at": (
                             leased.lease_expires_at.isoformat()
                             if leased.lease_expires_at else None
                         )},
            ))

        return snapshot.workflow_state

    # ------------------------------------------------------------------
    # Approval resume
    # ------------------------------------------------------------------

    async def resume_from_approval(self, request_id: str) -> PlannerResult:
        """Resume a paused workflow after an approval decision.

        If the request was approved: execute the paused DAG fragment and
        continue the iterative planning loop from that checkpoint.

        If the request was rejected: terminate safely without re-executing
        anything.

        Works both in-process (``InMemoryApprovalStore``) and after a
        process restart (``PersistentWorkflowStore`` loaded via
        ``restore_workflow()``).

        Raises:
        - ``RuntimeError`` if no paused state exists or no store is configured.
        - :class:`~freya.governance.errors.WorkflowLeaseError` if this runner
          does not hold the execution lease (persistent store only).
        - :class:`~freya.governance.errors.WorkflowAlreadyResumedError` if the
          approval request is no longer in a resumable state.
        """
        if self._approval_store is None and self._persistent_store is None:
            raise RuntimeError(
                "No approval store configured on this runner. "
                "Provide an InMemoryApprovalStore or PersistentWorkflowStore."
            )
        if not hasattr(self, "_paused_dag"):
            raise RuntimeError("No paused workflow to resume.")

        # Look up the approval request — in-memory store takes priority.
        req = None
        if self._approval_store is not None:
            try:
                req = self._approval_store.get(request_id)
            except (KeyError, Exception):
                pass
        if req is None and self._persistent_store is not None:
            req = self._persistent_store.load_approval(request_id)
        if req is None:
            raise RuntimeError(f"ApprovalRequest '{request_id}' not found in any store.")

        # Lease check — only needed when a persistent store is configured.
        if self._persistent_store is not None and hasattr(self, "_paused_session_id"):
            _sid = self._paused_session_id
            if not self._persistent_store.has_valid_lease(_sid, self.runner_id):
                snap = self._persistent_store.load_snapshot(_sid)
                planner_trace_for_event = self._paused_trace
                planner_trace_for_event.events.append(PlannerEvent(
                    event_type="workflow_resume_rejected",
                    iteration=self._paused_iteration,
                    payload={
                        "session_id": _sid,
                        "runner_id": self.runner_id,
                        "reason": "lease_not_held",
                        "lease_owner": snap.lease_owner if snap else None,
                    },
                ))
                raise WorkflowLeaseError(
                    _sid,
                    f"Runner '{self.runner_id}' does not hold a valid lease "
                    f"(owner: {snap.lease_owner if snap else 'unknown'}).",
                )

        # Guard against resuming an already-completed/failed approval.
        if req.state not in (WorkflowState.APPROVED, WorkflowState.REJECTED):
            planner_trace_for_event = self._paused_trace
            planner_trace_for_event.events.append(PlannerEvent(
                event_type="workflow_resume_rejected",
                iteration=self._paused_iteration,
                payload={
                    "session_id": self._paused_session_id,
                    "runner_id": self.runner_id,
                    "reason": "already_resumed_or_invalid_state",
                    "state": req.state.value,
                },
            ))
            raise WorkflowAlreadyResumedError(
                self._paused_session_id, req.state.value
            )

        context = self._paused_context
        planner_trace = self._paused_trace
        iteration = self._paused_iteration
        session_id = self._paused_session_id
        goal = self._paused_goal
        recovery_counts = self._paused_recovery_counts
        total_tasks = self._paused_total_tasks
        max_iterations = self._paused_max_iterations
        dag = self._paused_dag
        snapshot_version = getattr(self, "_paused_snapshot_version", None)

        # Clean up paused state.
        for attr in (
            "_paused_dag", "_paused_context", "_paused_trace", "_paused_iteration",
            "_paused_session_id", "_paused_goal", "_paused_recovery_counts",
            "_paused_total_tasks", "_paused_max_iterations", "_paused_snapshot_version",
        ):
            try:
                delattr(self, attr)
            except AttributeError:
                pass

        if req.state == WorkflowState.REJECTED:
            _add_governance_obs(
                context,
                dag.tasks[0].task_id if dag.tasks else "unknown",
                "workflow rejected by governance",
            )
            planner_trace.events.append(PlannerEvent(
                event_type="workflow_rejected_by_governance",
                iteration=iteration,
                payload={"request_id": request_id},
            ))
            planner_trace.events.append(PlannerEvent(
                event_type="planner_terminated",
                iteration=iteration,
                payload={"reason": "governance_rejected_after_review"},
            ))
            planner_trace.status = "FAILED"
            planner_trace.termination_reason = "governance_rejected_after_review"
            planner_trace.end_time = time.time()
            planner_trace.iterations_completed = iteration
            return PlannerResult(
                session_id, goal, context, planner_trace,
                workflow_state=WorkflowState.REJECTED,
                approval_request_id=request_id,
            )

        # Approved — resume execution.
        _add_governance_obs(
            context,
            dag.tasks[0].task_id if dag.tasks else "unknown",
            "workflow resumed after approval",
        )
        planner_trace.events.append(PlannerEvent(
            event_type="workflow_resumed_after_approval",
            iteration=iteration,
            payload={"request_id": request_id},
        ))
        await self._emit(EventType.WORKFLOW_RESUMED_AFTER_APPROVAL, session_id,
                         iteration=iteration,
                         workflow_state=WorkflowState.APPROVED,
                         payload={"request_id": request_id, "runner_id": self.runner_id})
        planner_trace.termination_reason = None
        planner_trace.end_time = None

        termination_reason: str | None = None

        # Execute the approved DAG fragment first.
        planner_trace.events.append(PlannerEvent(
            event_type="planner_iteration",
            iteration=iteration,
            payload={"tasks": [t.task_id for t in dag.tasks], "task_count": len(dag.tasks)},
        ))

        dag_result = await self._dag_runner.run(dag, memory=self._memory, session_id=session_id)

        new_obs: list[Observation] = []
        for task_id, task_result in dag_result.results.items():
            context.task_results[task_id] = {
                "status": task_result.status,
                "output": task_result.output,
                "error": task_result.error,
            }
            if task_result.status == "SUCCESS":
                context.completed_tasks.append(task_id)
            else:
                context.failed_tasks.append(task_id)
            task_type = "unknown"
            for t in dag.tasks:
                if t.task_id == task_id:
                    task_type = t.type
                    break
            obs = Observation.from_task_result(
                task_id=task_id,
                task_type=task_type,
                status=task_result.status,
                output=task_result.output,
                error=_sanitize_error(task_result.error),
            )
            context.recent_observations.append(obs)
            new_obs.append(obs)

        planner_trace.events.append(PlannerEvent(
            event_type="planner_observations_updated",
            iteration=iteration,
            payload={
                "observation_count": len(context.recent_observations),
                "new_observations": [o.as_summary() for o in new_obs],
            },
        ))

        if dag_result.dag_trace:
            context.trace_summary[f"iteration_{iteration}"] = {
                "status": dag_result.dag_trace.status,
                "task_count": len(dag_result.dag_trace.task_traces),
            }

        if dag_result.status == "FAILED":
            recovery_outcome = await self._handle_runtime_failures(
                dag=dag,
                dag_result=dag_result,
                context=context,
                planner_trace=planner_trace,
                iteration=iteration,
                recovery_counts=recovery_counts,
                session_id=session_id,
                goal=goal,
            )
            if recovery_outcome == "terminate":
                return PlannerResult(
                    session_id, goal, context, planner_trace,
                    workflow_state=WorkflowState.FAILED,
                    approval_request_id=request_id,
                )

        # Continue the planning loop from the next iteration.
        start_iteration = iteration + 1
        for iteration in range(start_iteration, max_iterations):
            context.iteration_count = iteration
            context.memory_snapshot = {
                key: self._memory.get(session_id, key)
                for key in self._memory.list_keys(session_id)
            }

            compressed = build_planner_context(context)
            planner_trace.events.append(PlannerEvent(
                event_type="planner_context_built",
                iteration=iteration,
                payload={
                    "observation_summaries": compressed["recent_observation_summaries"],
                    "memory_summary": compressed["memory_summary"],
                },
            ))

            try:
                candidate = await self._planner.plan_next(context)
            except Exception as exc:
                logger.warning("planner.plan_next raised: %s", exc)
                planner_trace.events.append(PlannerEvent(
                    event_type="planner_terminated",
                    iteration=iteration,
                    payload={"reason": "planner_plan_next_failed", "error": str(exc)},
                ))
                planner_trace.status = "FAILED"
                planner_trace.termination_reason = "planner_plan_next_failed"
                planner_trace.end_time = time.time()
                planner_trace.iterations_completed = iteration
                return PlannerResult(
                    session_id, goal, context, planner_trace,
                    workflow_state=WorkflowState.FAILED,
                    approval_request_id=request_id,
                )

            if not candidate.tasks:
                termination_reason = "planner_returned_empty_dag"
                planner_trace.events.append(PlannerEvent(
                    event_type="planner_terminated",
                    iteration=iteration,
                    payload={"reason": termination_reason},
                ))
                break

            vr = validate_dag_fragment(candidate, self._tool_registry, context)
            if not vr.valid:
                # Single repair attempt.
                issues_text = vr.as_text()
                planner_trace.events.append(PlannerEvent(
                    event_type="planner_validation_failed",
                    iteration=iteration,
                    payload={"issues": [i.model_dump() for i in vr.issues], "attempt": 0},
                ))
                try:
                    repaired = await self._planner.repair_dag(context, candidate, issues_text)
                    rvr = validate_dag_fragment(repaired, self._tool_registry, context)
                    if rvr.valid:
                        candidate = repaired
                    else:
                        planner_trace.events.append(PlannerEvent(
                            event_type="planner_repair_failed",
                            iteration=iteration,
                            payload={"issues": [i.model_dump() for i in rvr.issues]},
                        ))
                        planner_trace.status = "FAILED"
                        planner_trace.termination_reason = "dag_validation_failed_after_repair"
                        planner_trace.end_time = time.time()
                        planner_trace.iterations_completed = iteration
                        return PlannerResult(
                            session_id, goal, context, planner_trace,
                            workflow_state=WorkflowState.FAILED,
                            approval_request_id=request_id,
                        )
                except Exception as exc:
                    planner_trace.status = "FAILED"
                    planner_trace.termination_reason = "repair_failed"
                    planner_trace.end_time = time.time()
                    planner_trace.iterations_completed = iteration
                    return PlannerResult(
                        session_id, goal, context, planner_trace,
                        workflow_state=WorkflowState.FAILED,
                        approval_request_id=request_id,
                    )

            dag = candidate
            total_tasks += len(dag.tasks)
            if total_tasks > MAX_TOTAL_TASKS:
                planner_trace.status = "FAILED"
                planner_trace.termination_reason = "max_total_tasks_exceeded"
                planner_trace.end_time = time.time()
                planner_trace.iterations_completed = iteration
                return PlannerResult(
                    session_id, goal, context, planner_trace,
                    workflow_state=WorkflowState.FAILED,
                    approval_request_id=request_id,
                )

            # Re-evaluate governance on each resumed iteration.
            if self._governance is not None:
                gov_decision = self._governance.evaluate(context, dag)
                for policy_name in gov_decision.triggered_policies:
                    planner_trace.events.append(PlannerEvent(
                        event_type="governance_policy_triggered",
                        iteration=iteration,
                        payload={"policy": policy_name},
                    ))
                planner_trace.events.append(PlannerEvent(
                    event_type="governance_evaluated",
                    iteration=iteration,
                    payload={
                        "decision": gov_decision.decision.value,
                        "reason": gov_decision.reason,
                        "risk_level": gov_decision.risk_level,
                        "triggered_policies": gov_decision.triggered_policies,
                    },
                ))

                if gov_decision.decision == InterventionDecision.REQUIRE_APPROVAL:
                    obs_summaries = [o.as_summary() for o in context.recent_observations if o.semantic_summary]
                    new_req = ApprovalRequest(
                        session_id=session_id,
                        iteration=iteration,
                        proposed_dag=dag.model_dump(),
                        governance_reason=gov_decision.reason,
                        risk_level=gov_decision.risk_level,
                        triggered_policies=gov_decision.triggered_policies,
                        observation_summaries=obs_summaries,
                    )
                    if self._approval_store is not None:
                        self._approval_store.create(new_req)
                    _add_governance_obs(
                        context,
                        dag.tasks[0].task_id if dag.tasks else "unknown",
                        "workflow paused awaiting approval due to governance policy",
                    )
                    planner_trace.events.append(PlannerEvent(
                        event_type="workflow_paused_for_approval",
                        iteration=iteration,
                        payload={"request_id": new_req.request_id, "risk_level": gov_decision.risk_level},
                    ))
                    self._paused_dag = dag
                    self._paused_context = context
                    self._paused_trace = planner_trace
                    self._paused_iteration = iteration
                    self._paused_session_id = session_id
                    self._paused_goal = goal
                    self._paused_recovery_counts = recovery_counts
                    self._paused_total_tasks = total_tasks
                    self._paused_max_iterations = max_iterations
                    planner_trace.termination_reason = "paused_for_approval"
                    planner_trace.end_time = time.time()
                    planner_trace.iterations_completed = iteration
                    return PlannerResult(
                        session_id, goal, context, planner_trace,
                        workflow_state=WorkflowState.PAUSED_FOR_APPROVAL,
                        approval_request_id=new_req.request_id,
                    )

            planner_trace.events.append(PlannerEvent(
                event_type="planner_iteration",
                iteration=iteration,
                payload={"tasks": [t.task_id for t in dag.tasks], "task_count": len(dag.tasks)},
            ))

            dag_result = await self._dag_runner.run(dag, memory=self._memory, session_id=session_id)

            new_obs = []
            for task_id, task_result in dag_result.results.items():
                context.task_results[task_id] = {
                    "status": task_result.status,
                    "output": task_result.output,
                    "error": task_result.error,
                }
                if task_result.status == "SUCCESS":
                    context.completed_tasks.append(task_id)
                else:
                    context.failed_tasks.append(task_id)
                task_type = "unknown"
                for t in dag.tasks:
                    if t.task_id == task_id:
                        task_type = t.type
                        break
                obs = Observation.from_task_result(
                    task_id=task_id,
                    task_type=task_type,
                    status=task_result.status,
                    output=task_result.output,
                    error=_sanitize_error(task_result.error),
                )
                context.recent_observations.append(obs)
                new_obs.append(obs)

            planner_trace.events.append(PlannerEvent(
                event_type="planner_observations_updated",
                iteration=iteration,
                payload={
                    "observation_count": len(context.recent_observations),
                    "new_observations": [o.as_summary() for o in new_obs],
                },
            ))

            if dag_result.dag_trace:
                context.trace_summary[f"iteration_{iteration}"] = {
                    "status": dag_result.dag_trace.status,
                    "task_count": len(dag_result.dag_trace.task_traces),
                }

            if dag_result.status == "FAILED":
                recovery_outcome = await self._handle_runtime_failures(
                    dag=dag,
                    dag_result=dag_result,
                    context=context,
                    planner_trace=planner_trace,
                    iteration=iteration,
                    recovery_counts=recovery_counts,
                    session_id=session_id,
                    goal=goal,
                )
                if recovery_outcome == "terminate":
                    return PlannerResult(
                        session_id, goal, context, planner_trace,
                        workflow_state=WorkflowState.FAILED,
                        approval_request_id=request_id,
                    )
        else:
            termination_reason = "max_iterations_reached"
            planner_trace.status = "MAX_ITERATIONS_REACHED"
            planner_trace.events.append(PlannerEvent(
                event_type="planner_terminated",
                iteration=max_iterations - 1,
                payload={"reason": termination_reason, "max_iterations": max_iterations},
            ))

        planner_trace.termination_reason = termination_reason
        planner_trace.end_time = time.time()
        planner_trace.iterations_completed = context.iteration_count + 1

        # Release lease on successful completion when backed by persistent store.
        if self._persistent_store is not None:
            try:
                self._persistent_store.release_lease(session_id, self.runner_id)
                planner_trace.events.append(PlannerEvent(
                    event_type="workflow_lease_released",
                    iteration=context.iteration_count,
                    payload={"session_id": session_id, "runner_id": self.runner_id},
                ))
            except Exception:
                pass  # Best-effort lease release; failure is non-fatal.

        await self._emit(EventType.WORKFLOW_COMPLETED, session_id,
                         iteration=context.iteration_count,
                         workflow_state=WorkflowState.COMPLETED,
                         payload={
                             "goal": goal,
                             "completed_tasks": list(context.completed_tasks),
                             "termination_reason": termination_reason,
                         })
        return PlannerResult(
            session_id, goal, context, planner_trace,
            workflow_state=WorkflowState.COMPLETED,
            approval_request_id=request_id,
        )

    # ------------------------------------------------------------------
    # Runtime failure recovery helper
    # ------------------------------------------------------------------

    async def _handle_runtime_failures(
        self,
        dag: "DAG",
        dag_result: object,
        context: PlanningContext,
        planner_trace: PlannerTrace,
        iteration: int,
        recovery_counts: dict[str, int],
        session_id: str,
        goal: str,
    ) -> str:
        """Classify, observe, and optionally recover from runtime task failures.

        Returns one of:
          ``"terminate"``  — runner should stop and return a FAILED result
          ``"recovered"``  — recovery succeeded; runner should continue
        """
        # Classify each failed task from this dag execution and annotate observations.
        failed_obs: list[Observation] = []
        for task_id, task_result in dag_result.results.items():  # type: ignore[attr-defined]
            if task_result.status == "SUCCESS":
                continue
            # Find the most recently appended observation for this task that
            # hasn't yet been classified (failure_category is None).
            obs = next(
                (
                    o for o in reversed(context.recent_observations)
                    if o.task_id == task_id
                    and o.status == "FAILED"
                    and o.failure_category is None
                ),
                None,
            )
            if obs is None:
                obs = Observation(
                    task_id=task_id,
                    task_type="tool",
                    status="FAILED",
                    error=_sanitize_error(task_result.error),  # type: ignore[attr-defined]
                )
                context.recent_observations.append(obs)
            cl = classify_failure(_sanitize_error(task_result.error) or "")  # type: ignore[attr-defined]
            obs.failure_category = cl["failure_category"]
            obs.recoverable = cl["recoverable"]
            if not obs.semantic_summary:
                obs.semantic_summary = cl["summary"]
            failed_obs.append(obs)
            planner_trace.events.append(PlannerEvent(
                event_type="runtime_failure_observed",
                iteration=iteration,
                payload={
                    "task_id": obs.task_id,
                    "failure_category": obs.failure_category,
                    "recoverable": obs.recoverable,
                    "summary": obs.semantic_summary,
                },
            ))

        if not failed_obs:
            # No observations to classify (shouldn't happen, but guard).
            return "terminate"

        # Check for non-recoverable failures first.
        non_recoverable = [o for o in failed_obs if not o.recoverable]
        if non_recoverable:
            planner_trace.events.append(PlannerEvent(
                event_type="runtime_failure_terminal",
                iteration=iteration,
                payload={
                    "task_ids": [o.task_id for o in non_recoverable],
                    "failure_categories": [o.failure_category for o in non_recoverable],
                },
            ))
            planner_trace.events.append(PlannerEvent(
                event_type="planner_terminated",
                iteration=iteration,
                payload={
                    "reason": "runtime_non_recoverable_failure",
                    "failed_tasks": [o.task_id for o in non_recoverable],
                },
            ))
            planner_trace.status = "FAILED"
            planner_trace.termination_reason = "runtime_non_recoverable_failure"
            planner_trace.end_time = time.time()
            planner_trace.iterations_completed = iteration + 1
            return "terminate"

        # Check per-task recovery limits.
        recoverable = [o for o in failed_obs if o.recoverable]
        limit_exceeded = [
            o for o in recoverable
            if recovery_counts.get(o.task_id, 0) >= MAX_RUNTIME_RECOVERY_ATTEMPTS
        ]
        if limit_exceeded:
            planner_trace.events.append(PlannerEvent(
                event_type="runtime_failure_terminal",
                iteration=iteration,
                payload={
                    "task_ids": [o.task_id for o in limit_exceeded],
                    "reason": "max_runtime_recovery_attempts_exceeded",
                },
            ))
            planner_trace.events.append(PlannerEvent(
                event_type="planner_terminated",
                iteration=iteration,
                payload={
                    "reason": "max_runtime_recovery_attempts_exceeded",
                    "task_ids": [o.task_id for o in limit_exceeded],
                },
            ))
            planner_trace.status = "FAILED"
            planner_trace.termination_reason = "max_runtime_recovery_attempts_exceeded"
            planner_trace.end_time = time.time()
            planner_trace.iterations_completed = iteration + 1
            return "terminate"

        # Increment recovery counters and mark observations.
        for o in recoverable:
            recovery_counts[o.task_id] = recovery_counts.get(o.task_id, 0) + 1
            o.recovery_attempted = True

        planner_trace.events.append(PlannerEvent(
            event_type="runtime_recovery_attempted",
            iteration=iteration,
            payload={
                "task_ids": [o.task_id for o in recoverable],
                "recovery_attempts": {o.task_id: recovery_counts[o.task_id] for o in recoverable},
            },
        ))

        # Ask the planner to generate a recovery DAG.
        try:
            recovery_dag = await self._planner.plan_recovery(context, recoverable)
        except Exception as exc:
            logger.warning("plan_recovery raised: %s", exc)
            planner_trace.events.append(PlannerEvent(
                event_type="runtime_recovery_failed",
                iteration=iteration,
                payload={"error": str(exc)},
            ))
            planner_trace.events.append(PlannerEvent(
                event_type="planner_terminated",
                iteration=iteration,
                payload={"reason": "recovery_plan_failed", "error": str(exc)},
            ))
            planner_trace.status = "FAILED"
            planner_trace.termination_reason = "recovery_plan_failed"
            planner_trace.end_time = time.time()
            planner_trace.iterations_completed = iteration + 1
            return "terminate"

        if not recovery_dag.tasks:
            # Planner signalled it cannot recover.
            planner_trace.events.append(PlannerEvent(
                event_type="runtime_recovery_failed",
                iteration=iteration,
                payload={"reason": "planner_returned_empty_recovery_dag"},
            ))
            planner_trace.events.append(PlannerEvent(
                event_type="planner_terminated",
                iteration=iteration,
                payload={"reason": "planner_returned_empty_recovery_dag"},
            ))
            planner_trace.status = "FAILED"
            planner_trace.termination_reason = "planner_returned_empty_recovery_dag"
            planner_trace.end_time = time.time()
            planner_trace.iterations_completed = iteration + 1
            return "terminate"

        # Execute recovery DAG.
        recovery_result = await self._dag_runner.run(
            recovery_dag, memory=self._memory, session_id=session_id
        )

        # Collect recovery execution observations.
        for task_id, task_result in recovery_result.results.items():
            task_type = "unknown"
            for t in recovery_dag.tasks:
                if t.task_id == task_id:
                    task_type = t.type
                    break
            rec_obs = Observation.from_task_result(
                task_id=task_id,
                task_type=task_type,
                status=task_result.status,
                output=task_result.output,
                error=_sanitize_error(task_result.error),
            )
            rec_obs.recovery_attempted = True
            context.recent_observations.append(rec_obs)
            if task_result.status == "SUCCESS":
                if task_id not in context.completed_tasks:
                    context.completed_tasks.append(task_id)
                if task_id in context.failed_tasks:
                    context.failed_tasks.remove(task_id)
                context.task_results[task_id] = {
                    "status": task_result.status,
                    "output": task_result.output,
                    "error": task_result.error,
                }
            else:
                if task_id not in context.failed_tasks:
                    context.failed_tasks.append(task_id)

        if recovery_result.status == "SUCCESS":
            planner_trace.events.append(PlannerEvent(
                event_type="runtime_recovery_succeeded",
                iteration=iteration,
                payload={
                    "task_ids": [o.task_id for o in recoverable],
                    "recovery_tasks": [t.task_id for t in recovery_dag.tasks],
                },
            ))
            return "recovered"

        # Recovery DAG also failed.
        planner_trace.events.append(PlannerEvent(
            event_type="runtime_recovery_failed",
            iteration=iteration,
            payload={
                "task_ids": [o.task_id for o in recoverable],
                "recovery_tasks": [t.task_id for t in recovery_dag.tasks],
            },
        ))
        planner_trace.events.append(PlannerEvent(
            event_type="planner_terminated",
            iteration=iteration,
            payload={"reason": "recovery_dag_execution_failed"},
        ))
        planner_trace.status = "FAILED"
        planner_trace.termination_reason = "recovery_dag_execution_failed"
        planner_trace.end_time = time.time()
        planner_trace.iterations_completed = iteration + 1
        return "terminate"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_error(error: str | None) -> str | None:
    """Strip raw tracebacks from an error string before exposing to the planner.

    Keeps only the first meaningful line (up to the first blank line or the
    first 'Traceback' line), then truncates to 200 chars.
    """
    if not error:
        return error
    lines = error.splitlines()
    clean_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Traceback") or stripped.startswith("File "):
            break
        if stripped:
            clean_lines.append(stripped)
    cleaned = " | ".join(clean_lines) if clean_lines else error.splitlines()[0]
    return cleaned[:200]


def _add_repair_obs(
    context: PlanningContext,
    task_id: str,
    reason: str,
    repair_attempted: bool = True,
) -> None:
    """Append a synthetic repair observation to PlanningContext."""
    obs = Observation(
        task_id=task_id,
        task_type="plan",
        status="FAILED",
        error=reason,
        semantic_summary=reason,
        repair_attempted=repair_attempted,
        repair_reason=reason,
    )
    context.recent_observations.append(obs)


def _add_recovery_obs(
    context: PlanningContext,
    task_id: str,
    reason: str,
    failure_category: str = "TOOL_EXCEPTION",
) -> None:
    """Append a synthetic runtime-recovery observation to PlanningContext."""
    obs = Observation(
        task_id=task_id,
        task_type="tool",
        status="FAILED",
        error=reason,
        semantic_summary=reason,
        failure_category=failure_category,
        recoverable=True,
        recovery_attempted=True,
    )
    context.recent_observations.append(obs)


def _add_governance_obs(
    context: PlanningContext,
    task_id: str,
    summary: str,
) -> None:
    """Append a governance advisory observation to PlanningContext."""
    obs = Observation(
        task_id=task_id,
        task_type="governance",
        status="ADVISORY",
        semantic_summary=summary,
    )
    context.recent_observations.append(obs)
