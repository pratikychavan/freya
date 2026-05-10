"""examples/experience_layer_demo.py

Freya SDK — Experience Abstraction Layer Demo
Step 29b: Human-Centered Governed Workflow UX

Demonstrates:
  Scenario AL — User-Friendly Progress
  Scenario AM — Approval Experience
  Scenario AN — Narrative Summary (LLM + deterministic fallback)
  Scenario AO — Progressive Disclosure (user / power-user / engineer views)
  Scenario AP — Session Continuity (pause → restore → resume lifecycle)

Usage:
    OPENROUTER_API_KEY=<key> python examples/experience_layer_demo.py

The same real Freya runtime is used throughout — only the presentation
layer changes between scenarios.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.WARNING)
logging.getLogger("freya").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# Freya SDK — runtime imports
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
from freya.planner.runner import IterativePlannerRunner
from freya.economics.engine import ExecutionEconomicsEngine
from freya.economics.models import WorkflowBudget, WorkflowPriority
from freya.strategies.timeline import render_strategy_timeline

# ---------------------------------------------------------------------------
# Freya SDK — experience layer imports
# ---------------------------------------------------------------------------
from freya.experience import (
    RuntimeEventTranslator,
    ApprovalExperienceBuilder,
    NarrativeSummaryGenerator,
    WorkflowProgressTracker,
    build_progress_from_events,
    render_user_view,
    render_power_user_view,
    render_engineer_view,
)

# ---------------------------------------------------------------------------
# Demo travel modules
# ---------------------------------------------------------------------------
from freya.demo.model_routing import MODEL_ROUTING, TIMEOUT_SECONDS
from freya.demo.datasets import PREFERRED_HOTEL_BUDGET_PER_NIGHT_INR, TOTAL_TRIP_BUDGET_INR
from freya.demo.openrouter_client import OpenRouterAdapter
from freya.demo.tools import (
    SearchPrimaryFlightsTool, SearchAlternativeFlightsTool,
    SearchHotelsTool, CompareHotelsTool, BuildItineraryTool, EstimateCostsTool,
)
from freya.demo.planner import TravelPlanner
from freya.demo.governance import HotelOverBudgetPolicy, TravelStrategyEngine


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

_W = 72


def _banner(title: str) -> str:
    bar = "═" * _W
    inner = f"  {title}  "
    pad = _W - len(inner)
    return f"\n╔{bar}╗\n║{inner}{' ' * pad}║\n╚{bar}╝\n"


def _scenario(label: str, title: str) -> str:
    return (
        f"\n{'─' * _W}\n"
        f"  {label}  {title}\n"
        f"{'─' * _W}\n"
    )


def _divider() -> str:
    return "─" * _W


# ---------------------------------------------------------------------------
# Event collector
# ---------------------------------------------------------------------------

class EventCollector:
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
# Shared runtime setup (used by all scenarios)
# ---------------------------------------------------------------------------

def _build_runtime(api_key: str, tmp_dir: str) -> dict:
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
    adapter_sum = OpenRouterAdapter(
        model=MODEL_ROUTING.get("summarization", MODEL_ROUTING["deterministic"]),
        api_key=api_key,
        timeout=TIMEOUT_SECONDS.get("summarization", 30.0),
    )

    primary_flights = SearchPrimaryFlightsTool()
    alt_flights     = SearchAlternativeFlightsTool()
    hotel_search    = SearchHotelsTool()
    hotel_compare   = CompareHotelsTool(cognitive_adapter=adapter_cog)
    itinerary       = BuildItineraryTool()
    costs           = EstimateCostsTool()

    registry = ToolRegistry()
    for tool in [primary_flights, alt_flights, hotel_search, hotel_compare, itinerary, costs]:
        registry.register(tool)

    governance = GovernanceEngine()
    governance.register(HotelOverBudgetPolicy(
        budget_per_night_inr=PREFERRED_HOTEL_BUDGET_PER_NIGHT_INR,
        nights=2,
    ))
    approval_store = InMemoryApprovalStore()
    persistent_store = PersistentWorkflowStore(tmp_dir)

    bus = InProcessEventBus()
    collector = EventCollector()
    bus.subscribe(collector)

    budget = WorkflowBudget(max_token_cost=50_000, max_estimated_cost=5.0)
    economics = ExecutionEconomicsEngine(budget=budget, priority=WorkflowPriority.NORMAL)
    strategy_engine = TravelStrategyEngine(economics_engine=economics)

    coordinator = WorkflowCoordinator()
    planner = TravelPlanner()
    engine = ExecutionEngine(llm_adapter=adapter_det, tool_registry=registry)
    dag_runner = DAGRunner(engine)
    memory = InMemoryStore()

    return {
        "adapter_det": adapter_det,
        "adapter_cog": adapter_cog,
        "adapter_sum": adapter_sum,
        "registry": registry,
        "governance": governance,
        "approval_store": approval_store,
        "persistent_store": persistent_store,
        "bus": bus,
        "collector": collector,
        "economics": economics,
        "strategy_engine": strategy_engine,
        "coordinator": coordinator,
        "planner": planner,
        "engine": engine,
        "dag_runner": dag_runner,
        "memory": memory,
    }


def _build_runner(rt: dict, runner_id: str) -> IterativePlannerRunner:
    return IterativePlannerRunner(
        planner=rt["planner"],
        dag_runner=rt["dag_runner"],
        tool_registry=rt["registry"],
        memory=rt["memory"],
        governance_engine=rt["governance"],
        approval_store=rt["approval_store"],
        persistent_store=rt["persistent_store"],
        runner_id=runner_id,
        event_bus=rt["bus"],
        coordinator=rt["coordinator"],
        strategy_engine=rt["strategy_engine"],
        economics_engine=rt["economics"],
    )


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

async def run_demo() -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("\n[ERROR] OPENROUTER_API_KEY is not set.\n")
        sys.exit(1)

    print(_banner("FREYA SDK — EXPERIENCE ABSTRACTION LAYER DEMO"))
    print("  Demonstrates human-centered UX layered over the real Freya runtime.\n")
    print(f"  Press Enter to step through each scenario, or Ctrl+C to exit.\n")

    goal = (
        "Plan a 2-day business trip to Bangalore next week. "
        "Budget ₹40,000. Need flights, hotel, and meeting itinerary."
    )

    tmp_dir = tempfile.mkdtemp(prefix="freya_exp_demo_")
    session_id = "exp-demo-" + str(uuid.uuid4())[:8]

    # ── Run the real workflow once (all scenarios share results) ─────────
    print("  Running BusinessTripPlanner workflow (real runtime)…\n")
    rt = _build_runtime(api_key, tmp_dir)
    runner = _build_runner(rt, "runner-" + str(uuid.uuid4())[:8])

    result = await runner.run(goal, session_id=session_id, max_iterations=10)
    phase1_trace = result.trace

    approval_req_id: str | None = None
    had_approval = False

    # Handle governance pause
    if result.workflow_state == WorkflowState.PAUSED_FOR_APPROVAL:
        approval_req_id = result.approval_request_id
        had_approval = True
        rt["approval_store"].approve(approval_req_id)
        rt["persistent_store"].release_lease(session_id, runner.runner_id)

        runner2 = _build_runner(rt, "runner-resume-" + str(uuid.uuid4())[:8])
        runner2.restore_workflow(session_id)
        result = await runner2.resume_from_approval(approval_req_id)

    all_events = rt["collector"].events

    # Determine recovery
    had_recovery = any(
        e.get("event_type") == "runtime_failure_observed" for e in all_events
    )

    final_ctx = result.final_context

    # ════════════════════════════════════════════════════════════════════
    # SCENARIO AL — User-Friendly Progress
    # ════════════════════════════════════════════════════════════════════
    input(_scenario("AL", "USER-FRIENDLY PROGRESS") + "  [Press Enter to display]\n")

    translator = RuntimeEventTranslator()
    updates = translator.translate_all(all_events)

    print("  What the user sees — translated runtime progress:\n")
    seen_titles: set[str] = set()
    for update in updates:
        if update.title not in seen_titles:
            print(update.render())
            seen_titles.add(update.title)
    print()

    # ════════════════════════════════════════════════════════════════════
    # SCENARIO AM — Approval Experience
    # ════════════════════════════════════════════════════════════════════
    input(_scenario("AM", "APPROVAL EXPERIENCE") + "  [Press Enter to display]\n")

    approval_builder = ApprovalExperienceBuilder()

    if approval_req_id:
        req = rt["approval_store"].get(approval_req_id)
        experience = approval_builder.build(req)
        print(approval_builder.render_terminal(experience))
    else:
        # Demonstrate with a synthetic approval request (no real pause occurred)
        from freya.governance.approval import ApprovalRequest
        synthetic_req = ApprovalRequest(
            session_id=session_id,
            iteration=3,
            proposed_dag={},
            governance_reason=(
                "Selected hotel 'Taj MG Road' costs ₹18,000/night (₹36,000 for 2 nights), "
                "exceeding preferred budget of ₹20,000 (₹10,000/night)."
            ),
            risk_level="medium",
            triggered_policies=["HotelOverBudgetPolicy"],
        )
        experience = approval_builder.build(synthetic_req)
        print("  (Synthetic example — hotel approval was auto-approved in this run)\n")
        print(approval_builder.render_terminal(experience))

    # ════════════════════════════════════════════════════════════════════
    # SCENARIO AN — Narrative Summary
    # ════════════════════════════════════════════════════════════════════
    input(_scenario("AN", "NARRATIVE SUMMARY") + "  [Press Enter to display]\n")

    narrative_gen = NarrativeSummaryGenerator(llm_adapter=rt["adapter_sum"])
    narrative = await narrative_gen.generate(
        goal=goal,
        completed_tasks=final_ctx.completed_tasks,
        task_results=final_ctx.task_results,
        had_recovery=had_recovery,
        had_approval=had_approval,
        economics=rt["economics"],
    )

    print("  LLM-generated narrative (what a normal user reads):\n")
    print(narrative.render())
    print()

    # Also show deterministic fallback
    narrative_fallback_gen = NarrativeSummaryGenerator(llm_adapter=None)
    narrative_fallback = await narrative_fallback_gen.generate(
        goal=goal,
        completed_tasks=final_ctx.completed_tasks,
        task_results=final_ctx.task_results,
        had_recovery=had_recovery,
        had_approval=had_approval,
    )

    print("  Deterministic fallback (no LLM required):\n")
    print(narrative_fallback.render())
    print()

    # ════════════════════════════════════════════════════════════════════
    # SCENARIO AO — Progressive Disclosure
    # ════════════════════════════════════════════════════════════════════
    input(_scenario("AO", "PROGRESSIVE DISCLOSURE — 3 VIEW TIERS") + "  [Press Enter to display]\n")

    tracker = build_progress_from_events(all_events)
    tracker.from_completed_tasks(final_ctx.completed_tasks)

    # Continuity messages — added once, from events (deduplicated internally)

    # ── USER VIEW ──────────────────────────────────────────────────────
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  VIEW TIER 1 — USER VIEW  (what a traveler sees)           │")
    print("  └─────────────────────────────────────────────────────────────┘\n")
    print(render_user_view(goal, tracker, narrative))

    input("  [Press Enter for POWER USER VIEW]\n")

    # ── POWER USER VIEW ───────────────────────────────────────────────
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  VIEW TIER 2 — POWER USER VIEW  (ops / team leads)         │")
    print("  └─────────────────────────────────────────────────────────────┘\n")

    # Extract strategy changes from trace
    strategy_changes: list[tuple[int, str]] = []
    for ev in phase1_trace.events:
        if ev.event_type == "execution_strategy_selected":
            strategy_changes.append((ev.iteration, ev.payload.get("strategy", "unknown")))

    print(render_power_user_view(
        goal=goal,
        tracker=tracker,
        narrative=narrative,
        economics=rt["economics"],
        strategy_changes=strategy_changes,
    ))

    input("  [Press Enter for ENGINEER VIEW]\n")

    # ── ENGINEER VIEW ─────────────────────────────────────────────────
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  VIEW TIER 3 — ENGINEER VIEW  (full observability)         │")
    print("  └─────────────────────────────────────────────────────────────┘\n")

    timeline_str = render_strategy_timeline(phase1_trace)

    print(render_engineer_view(
        goal=goal,
        all_events=all_events,
        economics=rt["economics"],
        strategy_timeline_str=timeline_str,
        governance_events=all_events,
    ))

    # ════════════════════════════════════════════════════════════════════
    # SCENARIO AP — Session Continuity
    # ════════════════════════════════════════════════════════════════════
    input(_scenario("AP", "SESSION CONTINUITY — HUMAN-READABLE LIFECYCLE") + "  [Press Enter to display]\n")

    print("  How Freya keeps users informed through the workflow lifecycle:\n")

    lifecycle_msgs = [
        ("started",   "▶  Trip planning started."),
        ("running",   "⟳  Searching flights…"),
        ("warning",   "⚠  Primary flight provider unavailable. Switching automatically."),
        ("running",   "⟳  Found flights via alternate provider. Continuing."),
        ("running",   "⟳  Comparing hotel options with AI reasoning…"),
        ("paused",    "⏸  Trip planning paused — your approval is needed."),
        ("running",   "▶  Approval received. Resuming trip planning."),
        ("restored",  "♻  Workflow state restored from saved checkpoint."),
        ("running",   "⟳  Building your meeting itinerary…"),
        ("running",   "⟳  Calculating total trip costs…"),
        ("completed", "✅  Trip planning completed successfully."),
    ]

    for status, msg in lifecycle_msgs:
        print(f"  {msg}")

    print()
    print("  Contrast with raw runtime events (engineer view):\n")
    raw_sample = [
        "  planner_iteration_started",
        "  execution_strategy_selected {strategy: deterministic}",
        "  tool_call_started {tool_name: search_primary_flights}",
        "  runtime_failure_observed {task_id: search_primary_flights}",
        "  execution_strategy_selected {strategy: recovery}",
        "  tool_call_completed {tool_name: search_alternative_flights}",
        "  execution_strategy_selected {strategy: cognitive}",
        "  governance_evaluated {decision: REQUIRE_APPROVAL}",
        "  workflow_paused_for_approval {request_id: ...}",
        "  workflow_resumed_after_approval",
        "  workflow_snapshot_restored {version: 1}",
        "  tool_call_completed {tool_name: build_itinerary}",
        "  tool_call_completed {tool_name: estimate_costs}",
        "  workflow_completed",
    ]
    for line in raw_sample:
        print(f"  \033[2m{line}\033[0m")  # dim/grey for contrast

    print()
    print(_divider())
    print("  Experience Layer Demo complete.")
    print(_divider())
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(run_demo())
