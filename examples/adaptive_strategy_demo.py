"""examples/adaptive_strategy_demo.py

Demonstrates the Adaptive Execution Strategy System (Step 27).

Scenarios:
  A — Deterministic: simple execution, no escalation.
  B — Repair Escalation: validation failures cause strategy switch to repair.
  C — Runtime Recovery: runtime failure triggers recovery strategy.
  D — Cognitive Escalation: low-confidence score forces cognitive mode.
  E — Forced HITL: repeated failures trigger governance human-approval.
  F — Safe Termination: too many recovery attempts → terminate.
  G — Strategy Persistence: pause → restore → strategy history survives.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile

# ---------------------------------------------------------------------------
# Add project root to path when running directly from examples/
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from freya.strategies.engine import ExecutionStrategyEngine
from freya.strategies.signals import RuntimeSignals
from freya.strategies.models import ExecutionStrategy
from freya.strategies.policies import (
    CognitiveEscalationPolicy,
    ForcedHumanApprovalPolicy,
    MaxRecoveryAttemptsPolicy,
    TerminationEscalationPolicy,
)
from freya.strategies.timeline import render_strategy_timeline
from freya.planner.trace import PlannerEvent, PlannerTrace


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _section(title: str) -> None:
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print(f"{'═' * 60}")


def _print_decision(decision, prefix: str = "  ") -> None:
    print(f"{prefix}strategy  : {decision.strategy.value}")
    print(f"{prefix}reason    : {decision.reason}")
    print(f"{prefix}confidence: {decision.confidence}")
    print(f"{prefix}triggered : {decision.triggered_by}")
    if decision.governance_constraints:
        print(f"{prefix}constraints: {decision.governance_constraints}")


def _build_trace_with_strategy_events(
    session_id: str,
    goal: str,
    iteration_data: list[dict],
) -> PlannerTrace:
    """Build a PlannerTrace with execution_strategy_selected events for timeline rendering."""
    trace = PlannerTrace(session_id=session_id, goal=goal)
    for item in iteration_data:
        trace.events.append(PlannerEvent(
            event_type="execution_strategy_selected",
            iteration=item["iteration"],
            payload={
                "strategy": item["strategy"],
                "reason": item.get("reason", ""),
                "confidence": item.get("confidence"),
                "triggered_by": item.get("triggered_by", []),
            },
        ))
        if "outcome_event" in item:
            trace.events.append(PlannerEvent(
                event_type=item["outcome_event"],
                iteration=item["iteration"],
                payload=item.get("outcome_payload", {}),
            ))
    trace.iterations_completed = len(iteration_data)
    trace.status = "SUCCESS"
    trace.termination_reason = iteration_data[-1].get("outcome_event") or "planner_returned_empty_dag"
    return trace


# ═══════════════════════════════════════════════════════════════════════
# Scenario A — Deterministic First
# ═══════════════════════════════════════════════════════════════════════

async def scenario_a() -> None:
    _section("Scenario A — Deterministic First")
    print("  Signals: no failures, high confidence  →  expect DETERMINISTIC\n")

    engine = ExecutionStrategyEngine()
    signals = RuntimeSignals()

    decision = engine.select_strategy(
        planning_context=object(),
        workflow_state=None,
        runtime_signals=signals,
    )
    _print_decision(decision)

    assert decision.strategy == ExecutionStrategy.DETERMINISTIC, (
        f"Expected DETERMINISTIC, got {decision.strategy}"
    )

    trace = _build_trace_with_strategy_events(
        "session-a", "book a flight",
        [{"iteration": 0, "strategy": "deterministic", "confidence": 1.0,
          "reason": "No escalation signals.", "outcome_event": "planner_terminated",
          "outcome_payload": {"reason": "planner_returned_empty_dag"}}],
    )
    print()
    print(render_strategy_timeline(trace))
    print("\n  ✓ Scenario A passed.")


# ═══════════════════════════════════════════════════════════════════════
# Scenario B — Repair Escalation
# ═══════════════════════════════════════════════════════════════════════

async def scenario_b() -> None:
    _section("Scenario B — Repair Escalation")
    print("  Signals: 1 validation failure  →  expect REPAIR\n")

    engine = ExecutionStrategyEngine()
    signals = RuntimeSignals(validation_failures=1)

    decision = engine.select_strategy(None, None, signals)
    _print_decision(decision)

    assert decision.strategy == ExecutionStrategy.REPAIR

    trace = _build_trace_with_strategy_events(
        "session-b", "process expense report",
        [
            {"iteration": 0, "strategy": "deterministic", "confidence": 1.0,
             "reason": "No escalation signals.",
             "outcome_event": "planner_validation_failed",
             "outcome_payload": {"issues": ["missing_required_field"]}},
            {"iteration": 1, "strategy": "repair", "confidence": 0.85,
             "reason": "1 validation failure. Switching to repair.",
             "triggered_by": ["validation_failures_present"],
             "outcome_event": "planner_repair_succeeded",
             "outcome_payload": {}},
        ],
    )
    print()
    print(render_strategy_timeline(trace))
    print("\n  ✓ Scenario B passed.")


# ═══════════════════════════════════════════════════════════════════════
# Scenario C — Runtime Recovery
# ═══════════════════════════════════════════════════════════════════════

async def scenario_c() -> None:
    _section("Scenario C — Runtime Recovery")
    print("  Signals: 1 runtime failure  →  expect RECOVERY\n")

    engine = ExecutionStrategyEngine()
    signals = RuntimeSignals(runtime_failures=1)

    decision = engine.select_strategy(None, None, signals)
    _print_decision(decision)

    assert decision.strategy == ExecutionStrategy.RECOVERY

    trace = _build_trace_with_strategy_events(
        "session-c", "run database backup",
        [
            {"iteration": 0, "strategy": "deterministic", "confidence": 1.0,
             "reason": "No escalation signals.",
             "outcome_event": "runtime_failure_observed",
             "outcome_payload": {"error": "timeout"}},
            {"iteration": 1, "strategy": "recovery", "confidence": 0.85,
             "reason": "1 runtime failure. Attempting recovery.",
             "triggered_by": ["runtime_failures_present"],
             "outcome_event": "runtime_recovery_succeeded",
             "outcome_payload": {}},
        ],
    )
    print()
    print(render_strategy_timeline(trace))
    print("\n  ✓ Scenario C passed.")


# ═══════════════════════════════════════════════════════════════════════
# Scenario D — Cognitive Escalation
# ═══════════════════════════════════════════════════════════════════════

async def scenario_d() -> None:
    _section("Scenario D — Cognitive Escalation")
    print("  Signals: confidence_score=0.3 (below 0.5 threshold)  →  expect COGNITIVE\n")

    engine = ExecutionStrategyEngine(cognitive_confidence_threshold=0.5)
    signals = RuntimeSignals(confidence_score=0.3)

    decision = engine.select_strategy(None, None, signals)
    _print_decision(decision)

    assert decision.strategy == ExecutionStrategy.COGNITIVE

    # Also show CognitiveEscalationPolicy
    policy = CognitiveEscalationPolicy(validation_failure_threshold=2)
    policy_decision = policy.evaluate(
        RuntimeSignals(validation_failures=2),
        ExecutionStrategy.DETERMINISTIC,
    )
    print()
    print("  CognitiveEscalationPolicy fired:")
    _print_decision(policy_decision, prefix="    ")

    trace = _build_trace_with_strategy_events(
        "session-d", "analyze complex contract",
        [
            {"iteration": 0, "strategy": "deterministic", "confidence": 1.0,
             "reason": "No escalation.",
             "outcome_event": "planner_validation_failed",
             "outcome_payload": {}},
            {"iteration": 1, "strategy": "cognitive", "confidence": 0.8,
             "reason": "Confidence 0.3 below threshold. Escalating to cognitive.",
             "triggered_by": ["low_confidence_score"],
             "outcome_event": "planner_terminated",
             "outcome_payload": {"reason": "planner_returned_empty_dag"}},
        ],
    )
    print()
    print(render_strategy_timeline(trace))
    print("\n  ✓ Scenario D passed.")


# ═══════════════════════════════════════════════════════════════════════
# Scenario E — Forced HITL
# ═══════════════════════════════════════════════════════════════════════

async def scenario_e() -> None:
    _section("Scenario E — Forced HITL")
    print("  Signals: 1 pending approval  →  expect HUMAN_APPROVAL\n")

    engine = ExecutionStrategyEngine()
    signals = RuntimeSignals(pending_approvals=1)

    decision = engine.select_strategy(None, None, signals)
    _print_decision(decision)

    assert decision.strategy == ExecutionStrategy.HUMAN_APPROVAL

    # ForcedHumanApprovalPolicy illustration
    policy = ForcedHumanApprovalPolicy(failure_threshold=3)
    policy_decision = policy.evaluate(
        RuntimeSignals(validation_failures=1, runtime_failures=1, governance_blocks=1),
        ExecutionStrategy.DETERMINISTIC,
    )
    print()
    print("  ForcedHumanApprovalPolicy fired:")
    _print_decision(policy_decision, prefix="    ")

    trace = _build_trace_with_strategy_events(
        "session-e", "approve high-value wire transfer",
        [
            {"iteration": 0, "strategy": "deterministic", "confidence": 1.0,
             "reason": "No escalation.",
             "outcome_event": "workflow_paused_for_approval",
             "outcome_payload": {"risk_level": "HIGH"}},
            {"iteration": 1, "strategy": "human_approval", "confidence": 1.0,
             "reason": "1 approval pending. Paused for human review.",
             "triggered_by": ["pending_approvals"],
             "outcome_event": "workflow_resumed_after_approval",
             "outcome_payload": {}},
        ],
    )
    print()
    print(render_strategy_timeline(trace))
    print("\n  ✓ Scenario E passed.")


# ═══════════════════════════════════════════════════════════════════════
# Scenario F — Safe Termination
# ═══════════════════════════════════════════════════════════════════════

async def scenario_f() -> None:
    _section("Scenario F — Safe Termination")
    print("  Signals: 3 recovery attempts (max=2)  →  expect TERMINATE\n")

    engine = ExecutionStrategyEngine(max_recovery_attempts=2)
    signals = RuntimeSignals(recovery_attempts=3, runtime_failures=3)

    decision = engine.select_strategy(None, None, signals)
    _print_decision(decision)

    assert decision.strategy == ExecutionStrategy.TERMINATE

    # TerminationEscalationPolicy illustration
    policy = TerminationEscalationPolicy(max_total_failures=5)
    policy_decision = policy.evaluate(
        RuntimeSignals(
            validation_failures=2,
            runtime_failures=2,
            governance_blocks=1,
        ),
        ExecutionStrategy.RECOVERY,
    )
    print()
    print("  TerminationEscalationPolicy fired:")
    _print_decision(policy_decision, prefix="    ")

    trace = _build_trace_with_strategy_events(
        "session-f", "run unstable migration script",
        [
            {"iteration": 0, "strategy": "deterministic", "confidence": 1.0,
             "reason": "No escalation.",
             "outcome_event": "runtime_failure_observed", "outcome_payload": {}},
            {"iteration": 1, "strategy": "recovery", "confidence": 0.85,
             "reason": "1 runtime failure.",
             "triggered_by": ["runtime_failures_present"],
             "outcome_event": "runtime_recovery_failed", "outcome_payload": {}},
            {"iteration": 2, "strategy": "recovery", "confidence": 0.85,
             "reason": "2 runtime failures.",
             "triggered_by": ["runtime_failures_present"],
             "outcome_event": "runtime_recovery_failed", "outcome_payload": {}},
            {"iteration": 3, "strategy": "terminate", "confidence": 1.0,
             "reason": "Recovery attempts (3) exceed limit (2). Workflow unrecoverable.",
             "triggered_by": ["max_recovery_attempts_exceeded"],
             "outcome_event": "planner_terminated",
             "outcome_payload": {"reason": "strategy_terminated"}},
        ],
    )
    trace.status = "FAILED"
    trace.termination_reason = "strategy_terminated"
    print()
    print(render_strategy_timeline(trace))
    print("\n  ✓ Scenario F passed.")


# ═══════════════════════════════════════════════════════════════════════
# Scenario G — Strategy Persistence (pause/restore)
# ═══════════════════════════════════════════════════════════════════════

async def scenario_g() -> None:
    _section("Scenario G — Strategy Persistence")
    print("  Demonstrates strategy_history surviving pause → restore.\n")

    # Build strategy history that would be saved in WorkflowSnapshot
    strategy_history = [
        {
            "iteration": 0,
            "strategy": "deterministic",
            "reason": "No escalation signals.",
            "confidence": 1.0,
            "triggered_by": [],
            "governance_constraints": [],
        },
        {
            "iteration": 1,
            "strategy": "repair",
            "reason": "1 validation failure.",
            "confidence": 0.85,
            "triggered_by": ["validation_failures_present"],
            "governance_constraints": [],
        },
    ]

    current_strategy = strategy_history[-1]["strategy"]

    print(f"  Before pause:")
    print(f"    current_strategy  = {current_strategy!r}")
    print(f"    strategy_history  = {[h['strategy'] for h in strategy_history]}")

    # Simulate what WorkflowSnapshot stores
    snapshot_fields = {
        "current_strategy": current_strategy,
        "strategy_history": strategy_history,
    }

    # Simulate restore
    restored_current = snapshot_fields["current_strategy"]
    restored_history = snapshot_fields["strategy_history"]

    print(f"\n  After restore:")
    print(f"    restored current_strategy = {restored_current!r}")
    print(f"    restored strategy_history = {[h['strategy'] for h in restored_history]}")

    assert restored_current == "repair"
    assert len(restored_history) == 2
    assert restored_history[0]["strategy"] == "deterministic"
    assert restored_history[1]["strategy"] == "repair"

    # Continue from here with the engine on the restored signals
    engine = ExecutionStrategyEngine()
    # After restore the validation failure was fixed, so no signals now
    signals = RuntimeSignals()
    decision = engine.select_strategy(None, None, signals)
    print(f"\n  Post-restore strategy decision: {decision.strategy.value!r}")
    print(f"  reason: {decision.reason}")

    assert decision.strategy == ExecutionStrategy.DETERMINISTIC

    trace_items = [
        {"iteration": 0, "strategy": "deterministic", "confidence": 1.0,
         "reason": "No escalation.", "outcome_event": "workflow_paused_for_approval",
         "outcome_payload": {}},
        {"iteration": 1, "strategy": "repair", "confidence": 0.85,
         "reason": "1 validation failure.",
         "triggered_by": ["validation_failures_present"],
         "outcome_event": "workflow_snapshot_persisted", "outcome_payload": {}},
        {"iteration": 2, "strategy": "deterministic", "confidence": 1.0,
         "reason": "No escalation signals. Continuing with deterministic execution.",
         "outcome_event": "workflow_snapshot_restored", "outcome_payload": {}},
        {"iteration": 3, "strategy": "deterministic", "confidence": 1.0,
         "reason": "No escalation signals. Continuing with deterministic execution.",
         "outcome_event": "planner_terminated",
         "outcome_payload": {"reason": "planner_returned_empty_dag"}},
    ]
    trace = _build_trace_with_strategy_events("session-g", "process restored report", trace_items)
    print()
    print(render_strategy_timeline(trace))
    print("\n  ✓ Scenario G passed.")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

async def main() -> None:
    print("Freya SDK — Adaptive Execution Strategy Demo")
    print("Step 27: Adaptive Execution Strategy System\n")

    await scenario_a()
    await scenario_b()
    await scenario_c()
    await scenario_d()
    await scenario_e()
    await scenario_f()
    await scenario_g()

    print("\n" + "═" * 60)
    print("  All 7 scenarios passed successfully.")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
