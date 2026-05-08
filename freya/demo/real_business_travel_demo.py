"""examples/real_business_travel_demo.py

Freya SDK — Real Business Travel Coordinator Demo
Step 29: Governed Adaptive Execution on a Real Workflow

Demonstrates:
  ✓ Real IterativePlannerRunner orchestration
  ✓ Real OpenRouter LLM calls (different models per strategy)
  ✓ Flight provider failure + automatic recovery (alternate provider)
  ✓ Cognitive hotel comparison (real LLM reasoning via claude-3-haiku)
  ✓ Governance checkpoint (hotel over preferred budget → HITL approval)
  ✓ Workflow pause → snapshot persistence → restore → resume
  ✓ Execution economics tracking (tokens, cost, budget)
  ✓ Strategy timeline (deterministic → cognitive → human_approval → deterministic)
  ✓ Workflow tree rendering
  ✓ Clean terminal-friendly output

Usage:
    OPENROUTER_API_KEY=<key> python examples/real_business_travel_demo.py
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Logging configuration — suppress noisy framework logs for clean demo output
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.WARNING)
logging.getLogger("freya").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# Freya SDK imports
# ---------------------------------------------------------------------------
from freya.dag.runner import DAGRunner
from freya.engine import ExecutionEngine
from freya.registry import ToolRegistry
from freya.memory.store import InMemoryStore
from freya.governance.engine import GovernanceEngine
from freya.governance.store import InMemoryApprovalStore
from freya.governance.persistent_store import PersistentWorkflowStore
from freya.governance.state import WorkflowState
from freya.events.bus import InProcessEventBus
from freya.events.models import RuntimeEvent
from freya.workflows.coordinator import WorkflowCoordinator
from freya.workflows.tree import render_workflow_tree
from freya.planner.runner import IterativePlannerRunner
from freya.economics.engine import ExecutionEconomicsEngine
from freya.economics.models import WorkflowBudget, WorkflowPriority
from freya.strategies.timeline import render_strategy_timeline

# Demo-specific modules
from freya.demo.model_routing import MODEL_ROUTING, TIMEOUT_SECONDS
from freya.demo.datasets import (
    PREFERRED_HOTEL_BUDGET_PER_NIGHT_INR,
    TOTAL_TRIP_BUDGET_INR,
)
from freya.demo.openrouter_client import OpenRouterAdapter
from freya.demo.tools import (
    SearchPrimaryFlightsTool,
    SearchAlternativeFlightsTool,
    SearchHotelsTool,
    CompareHotelsTool,
    BuildItineraryTool,
    EstimateCostsTool,
)
from freya.demo.planner import TravelPlanner
from freya.demo.governance import HotelOverBudgetPolicy, TravelStrategyEngine
from freya.demo.rendering import (
    render_banner,
    render_request,
    render_event_stream,
    render_governance_section,
    render_final_plan,
    section,
    header,
    divider,
)
from freya.economics.visualization import render_execution_economics
from freya.strategies.timeline import render_strategy_timeline


# ---------------------------------------------------------------------------
# Event collector subscriber
# ---------------------------------------------------------------------------

class EventCollector:
    """Collects all RuntimeEvents for post-run rendering."""

    def __init__(self) -> None:
        self.events: list[dict] = []

    async def handle_event(self, event: RuntimeEvent) -> None:
        self.events.append({
            "event_type": event.event_type,
            "session_id": event.session_id,
            "iteration": event.iteration,
            "timestamp": event.timestamp.isoformat(),
            "payload": dict(event.payload),
        })


# ---------------------------------------------------------------------------
# Core demo runner
# ---------------------------------------------------------------------------

async def run_demo() -> None:
    # ── Validate API key ────────────────────────────────────────────────
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print(
            "\n[ERROR] OPENROUTER_API_KEY environment variable is not set.\n"
            "Export your key: export OPENROUTER_API_KEY=<your-key>\n"
        )
        sys.exit(1)

    print(render_banner())

    # ── Human input: trip request ────────────────────────────────────────
    default_goal = (
        "Plan a 2-day business trip to Bangalore next week. "
        "Budget ₹40,000. Need flights, hotel, and meeting itinerary."
    )
    print("  Enter your trip request (or press Enter to use the default):\n")
    print(f"    Default: {default_goal}\n")
    raw_goal = input("  > ").strip()
    goal = raw_goal if raw_goal else default_goal
    print()
    print(render_request(goal))

    # ── OpenRouter adapters (one per strategy tier) ─────────────────────
    adapter_det = OpenRouterAdapter(
        model=MODEL_ROUTING["deterministic"],
        api_key=api_key,
        timeout=TIMEOUT_SECONDS["deterministic"],
    )
    adapter_cog = OpenRouterAdapter(
        model=MODEL_ROUTING["cognitive"],
        api_key=api_key,
        timeout=TIMEOUT_SECONDS["cognitive"],
    )

    print(f"  Models configured:")
    print(f"    Deterministic : {adapter_det.model}")
    print(f"    Cognitive     : {adapter_cog.model}")
    print()

    # ── Tools ───────────────────────────────────────────────────────────
    primary_flights = SearchPrimaryFlightsTool()
    alt_flights     = SearchAlternativeFlightsTool()
    hotel_search    = SearchHotelsTool()
    hotel_compare   = CompareHotelsTool(cognitive_adapter=adapter_cog)
    itinerary       = BuildItineraryTool()
    costs           = EstimateCostsTool()

    registry = ToolRegistry()
    for tool in [primary_flights, alt_flights, hotel_search, hotel_compare, itinerary, costs]:
        registry.register(tool)

    # ── Governance ──────────────────────────────────────────────────────
    governance = GovernanceEngine()
    governance.register(HotelOverBudgetPolicy(
        budget_per_night_inr=PREFERRED_HOTEL_BUDGET_PER_NIGHT_INR,
        nights=2,
    ))
    approval_store = InMemoryApprovalStore()

    # ── Persistence (temp dir for demo) ─────────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="freya_travel_demo_")
    persistent_store = PersistentWorkflowStore(tmp_dir)

    # ── Event bus ───────────────────────────────────────────────────────
    bus = InProcessEventBus()
    collector = EventCollector()
    bus.subscribe(collector)

    # ── Execution economics ──────────────────────────────────────────────
    budget = WorkflowBudget(
        max_token_cost=50_000,
        max_estimated_cost=5.0,
    )
    economics = ExecutionEconomicsEngine(budget=budget, priority=WorkflowPriority.NORMAL)
    strategy_engine = TravelStrategyEngine(economics_engine=economics)

    # ── Workflow coordinator (workflow tree) ────────────────────────────
    coordinator = WorkflowCoordinator()

    # ── Planner + Engine + Runner ────────────────────────────────────────
    planner = TravelPlanner()
    engine  = ExecutionEngine(llm_adapter=adapter_det, tool_registry=registry)
    dag_runner = DAGRunner(engine)
    memory = InMemoryStore()

    root_session_id = "biz-trip-" + str(uuid.uuid4())[:8]

    runner = IterativePlannerRunner(
        planner=planner,
        dag_runner=dag_runner,
        tool_registry=registry,
        memory=memory,
        governance_engine=governance,
        approval_store=approval_store,
        persistent_store=persistent_store,
        runner_id="runner-" + str(uuid.uuid4())[:8],
        event_bus=bus,
        coordinator=coordinator,
        strategy_engine=strategy_engine,
        economics_engine=economics,
    )

    # ── Phase 1: Initial run ─────────────────────────────────────────────
    print(section("PHASE 1 — INITIAL EXECUTION"))
    print("  Running BusinessTripPlanner workflow...\n")
    print("  Steps that will execute:")
    print("    → search_primary_flights  [DETERMINISTIC — will fail, recovery activates]")
    print("    → search_alternative_flights  [DETERMINISTIC — recovery path]")
    print("    → search_hotels           [DETERMINISTIC]")
    print("    → compare_hotels          [COGNITIVE — real LLM reasoning]")
    print("    → build_itinerary         [DETERMINISTIC — governance fires here]")
    print()

    result = await runner.run(goal, session_id=root_session_id, max_iterations=10)
    phase1_trace = result.trace  # save before potential replacement

    # ── Phase 2: Handle governance pause ────────────────────────────────
    if result.workflow_state == WorkflowState.PAUSED_FOR_APPROVAL:
        approval_req_id = result.approval_request_id
        req = approval_store.get(approval_req_id)

        print(section("GOVERNANCE APPROVAL REQUIRED"))
        print()
        print(f"  ⏸  WORKFLOW PAUSED")
        print(f"     Request ID : {approval_req_id[:16]}…")
        print(f"     Reason     : {req.governance_reason}")
        print(f"     Risk level : {req.risk_level or 'medium'}")
        print(f"     Policies   : {', '.join(req.triggered_policies)}")
        print()
        print("  Snapshot persisted to:", tmp_dir)
        print()

        # ── Real HITL: ask the human ─────────────────────────────────────
        print("  " + "-" * 66)
        print("  OPERATOR DECISION REQUIRED")
        print("  " + "-" * 66)
        print("  Type  'approve'  to approve and resume the workflow.")
        print("  Type  'reject'   to reject and abort the workflow.")
        print("  Optionally add a reason after the decision, e.g.:")
        print("    approve  proximity justifies cost")
        print("    reject   select a cheaper hotel instead")
        print()

        while True:
            raw = input("  Decision > ").strip()
            if not raw:
                continue
            parts = raw.split(None, 1)
            decision = parts[0].lower()
            operator_reason = parts[1] if len(parts) > 1 else ""
            if decision in ("approve", "a", "yes", "y"):
                decision = "approve"
                break
            if decision in ("reject", "r", "no", "n", "deny"):
                decision = "reject"
                break
            print("  Please type 'approve' or 'reject'.")

        print()
        print(f"  Decision recorded : {decision.upper()}"
              + (f" — {operator_reason}" if operator_reason else ""))
        print()

        if decision == "reject":
            approval_store.reject(approval_req_id)
            print("  Workflow rejected by operator. Aborting.")
            print(divider())
            print("  Demo complete. Workflow: rejected")
            print(divider())
            return

        approval_store.approve(approval_req_id)

        # Release lease held by runner so runner2 can acquire it
        persistent_store.release_lease(root_session_id, runner.runner_id)

        # Restore workflow from snapshot
        runner2 = IterativePlannerRunner(
            planner=planner,
            dag_runner=dag_runner,
            tool_registry=registry,
            memory=memory,
            governance_engine=governance,
            approval_store=approval_store,
            persistent_store=persistent_store,
            runner_id="runner-resume-" + str(uuid.uuid4())[:8],
            event_bus=bus,
            coordinator=coordinator,
            strategy_engine=strategy_engine,
            economics_engine=economics,
        )

        print(section("PHASE 2 — RESTORE + RESUME"))
        print("  Restoring workflow from snapshot...")
        restored_state = runner2.restore_workflow(root_session_id)
        print(f"  Restored state : {restored_state.value}")
        print()

        result = await runner2.resume_from_approval(approval_req_id)
        print(f"  Resume result  : {result.workflow_state.value}")
        print()

    # ── Extract results from final context ──────────────────────────────
    ctx = result.final_context

    # Flight selection
    selected_flight: dict = {}
    for key in ("search_primary_flights", "search_alternative_flights"):
        r = ctx.task_results.get(key, {})
        flights = (r.get("output") or {}).get("flights", [])
        if flights:
            selected_flight = min(flights, key=lambda f: f.get("price_inr", 999_999))
            break

    # Hotel selection
    hotel_result = ctx.task_results.get("compare_hotels", {})
    hotel_output = (hotel_result.get("output") or {})
    selected_hotel: dict = hotel_output.get("selected_hotel", {})
    hotel_reasoning: str = hotel_output.get("reasoning", "")
    hotel_over_budget: bool = selected_hotel.get("price_per_night_inr", 0) > PREFERRED_HOTEL_BUDGET_PER_NIGHT_INR

    # Itinerary
    itin_result = ctx.task_results.get("build_itinerary", {})
    itin_output = (itin_result.get("output") or {})

    # Costs
    cost_result = ctx.task_results.get("estimate_costs", {})
    cost_output = (cost_result.get("output") or {})

    # ── Render all sections ──────────────────────────────────────────────

    print(section("WORKFLOW TREE"))
    print()
    if coordinator.get_children(root_session_id):
        tree = render_workflow_tree(coordinator, root_session_id, show_contracts=False)
        for line in tree.splitlines():
            print(f"  {line}")
    else:
        print(f"  {root_session_id}")
        print("    (single orchestrated workflow — no child delegations)")
    print()

    # Events
    all_events = collector.events
    print(render_event_stream(all_events))

    # Governance
    print(render_governance_section(all_events))

    # Strategy timeline
    print(section("STRATEGY TIMELINE"))
    print()
    timeline = render_strategy_timeline(phase1_trace)
    for line in timeline.splitlines():
        print(f"  {line}")
    print()

    # Economics
    print(section("EXECUTION ECONOMICS"))
    print()
    econ_report = render_execution_economics(economics)
    for line in econ_report.splitlines():
        print(f"  {line}")
    print()

    # Final plan
    if selected_flight and selected_hotel and itin_output:
        print(render_final_plan(
            selected_flight=selected_flight,
            selected_hotel=selected_hotel,
            hotel_reasoning=hotel_reasoning,
            itinerary=itin_output,
            cost_summary=cost_output,
            approved_over_budget=hotel_over_budget,
        ))
    else:
        # Partial results — show what we have
        print(header("PARTIAL RESULTS"))
        print()
        print(f"  Workflow state : {result.workflow_state.value}")
        print(f"  Completed tasks: {ctx.completed_tasks}")
        print(f"  Failed tasks   : {ctx.failed_tasks}")
        if selected_flight:
            print(f"  Flight         : {selected_flight.get('airline')} ₹{selected_flight.get('price_inr'):,}")
        if selected_hotel:
            print(f"  Hotel          : {selected_hotel.get('name')} ₹{selected_hotel.get('price_per_night_inr'):,}/night")
        print()

    print(divider())
    print(f"  Demo complete. Workflow: {result.workflow_state.value}")
    print(divider())
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(run_demo())
