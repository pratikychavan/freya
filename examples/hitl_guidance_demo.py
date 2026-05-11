"""examples/hitl_guidance_demo.py

Advanced HITL — Human Operational Guidance Demo
================================================

Scenarios:
  BI — Guidance Instead of Approval     : user steers instead of approving
  BJ — Steering Integration             : guidance changes workflow priorities
  BK — Optimization Reassessment        : optimization updates after guidance
  BL — Governance Review                : risky guidance blocked by governance
  BM — CLI Workflow Interaction         : professional interactive-style flow
  BN — Guidance Audit Trail             : full session history rendered

Run with:
    python examples/hitl_guidance_demo.py
"""
from __future__ import annotations

import asyncio

from freya.hitl import (
    GuidanceAuditTrail,
    GuidanceSession,
    HumanGuidanceGovernance,
    HumanGuidanceInterpreter,
)
from freya.hitl.rendering import render_guidance_result
from freya.optimization import OptimizationAdvisor, render_optimization_proposal
from freya.steering import SteeringCoordinator
from freya.steering.rendering import render_steering_state

# ── ANSI helpers ─────────────────────────────────────────────────────
_BOLD  = "\033[1m"
_DIM   = "\033[2m"
_CYAN  = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED   = "\033[91m"
_RESET = "\033[0m"


def _section(label: str) -> None:
    width = 70
    print()
    print(f"{_CYAN}{'═' * width}{_RESET}")
    print(f"{_BOLD}  {label}{_RESET}")
    print(f"{_CYAN}{'═' * width}{_RESET}")


def _freya_says(text: str) -> None:
    print(f"\n  {_DIM}Freya:{_RESET} {text}\n")


def _user_says(text: str) -> None:
    print(f"\n  {_DIM}User:{_RESET} {_YELLOW}\"{text}\"{_RESET}\n")


def _note(text: str) -> None:
    print(f"  {_DIM}[note]{_RESET} {_DIM}{text}{_RESET}")


# ── State factory ─────────────────────────────────────────────────────
def _mk_state(
    goal: str = "Plan Bangalore business trip",
    budget_inr: int = 50_000,
    nights: int = 3,
    strategy: str = "hybrid",
):
    return SteeringCoordinator.build_state(
        goal=goal,
        budget_inr=budget_inr,
        nights=nights,
        strategy=strategy,
    )


# ============================================================
# Scenario BI — Guidance Instead of Approval
# ============================================================
async def scenario_bi() -> None:
    _section("Scenario BI — Guidance Instead of Approval")

    _freya_says(
        "Hotel selection requires approval: ₹14,000/night × 3 nights = ₹42,000. "
        "This exceeds the ₹35,000 hotel sub-budget by ₹7,000."
    )

    state = _mk_state(budget_inr=50_000)
    session = GuidanceSession(state=state, session_id="BI-hotel-01")

    # Simulate: user chooses GUIDANCE instead of approve/reject
    _user_says("Find something slightly cheaper closer to metro access.")

    outcome, result = await session.run_checkpoint(
        context="Premium Hotel Selection",
        reason="Selected hotel exceeds preferred hotel budget by ₹7,000.",
        recommendation="Business hotel near client office — ₹14,000/night.",
        sim_choice="guidance",
        sim_guidance_text="Find something slightly cheaper closer to metro access.",
    )

    print(f"\n  Outcome: {_BOLD}{outcome}{_RESET}")
    _note("Workflow was steered instead of approved or rejected — execution continues with updated preferences.")


# ============================================================
# Scenario BJ — Steering Integration
# ============================================================
async def scenario_bj() -> None:
    _section("Scenario BJ — Steering Integration")

    state = _mk_state(budget_inr=45_000, strategy="cognitive")
    _freya_says("Workflow paused at transport selection. Current priority: balanced.")
    _note(f"Before guidance — strategy: {state.strategy}")

    print(render_steering_state(state))

    session = GuidanceSession(state=state, session_id="BJ-transport-01")

    _user_says("Prioritise convenience for this trip — shorter travel time matters more than cost.")

    outcome, result = await session.run_checkpoint(
        context="Transport Selection",
        reason="Multiple transport options available with different cost/time trade-offs.",
        recommendation="Mid-range taxi service — ₹2,800, 40 min.",
        sim_choice="guidance",
        sim_guidance_text="Prioritise convenience — shorter travel time matters more than cost.",
    )

    print(f"\n  Outcome: {_BOLD}{outcome}{_RESET}")
    _note(f"After guidance — strategy: {state.strategy}")
    print(render_steering_state(state))


# ============================================================
# Scenario BK — Optimization Reassessment
# ============================================================
async def scenario_bk() -> None:
    _section("Scenario BK — Optimization Reassessment")

    state = _mk_state(budget_inr=55_000, nights=4)
    advisor = OptimizationAdvisor()

    _freya_says("Running initial optimization scan…")
    proposal_before = advisor.propose(state)
    if proposal_before:
        print(render_optimization_proposal(proposal_before))
    else:
        print(f"  {_DIM}No initial opportunities detected.{_RESET}")

    session = GuidanceSession(state=state, session_id="BK-hotel-01")

    _user_says("Try to reduce the hotel cost — something around ₹8,000 per night is fine.")

    _freya_says("Applying budget guidance and reassessing optimization opportunities…")

    outcome, result = await session.run_checkpoint(
        context="Hotel Cost Review",
        reason="Current plan at ₹12,500/night may have budget-friendly alternatives.",
        recommendation="Current: Grand Mercure — ₹12,500/night × 4 = ₹50,000.",
        sim_choice="guidance",
        sim_guidance_text="Find something around ₹8,000 per night, good location.",
    )

    print(f"\n  Outcome: {_BOLD}{outcome}{_RESET}")
    _note("After guidance: OptimizationAdvisor.reassess() was triggered and output above shows new opportunities.")


# ============================================================
# Scenario BL — Governance Review (Blocked)
# ============================================================
async def scenario_bl() -> None:
    _section("Scenario BL — Governance Review (Blocked)")

    state = _mk_state(budget_inr=80_000)
    session = GuidanceSession(state=state, session_id="BL-gov-01")

    _freya_says(
        "Approval required: selected itinerary requires governance sign-off. "
        "Budget exceeds the ₹75,000 auto-approval threshold."
    )
    _user_says("Skip the approval for this one — just proceed.")

    outcome, result = await session.run_checkpoint(
        context="Governance Approval Checkpoint",
        reason="Total trip cost ₹82,000 exceeds governance auto-approval threshold (₹75,000).",
        recommendation="Escalate to manager for sign-off.",
        sim_choice="guidance",
        sim_guidance_text="Skip the approval step and just proceed.",
    )

    print(f"\n  Outcome: {_BOLD}{outcome}{_RESET}")
    _note("Governance override attempts are always blocked — the guidance was rejected at the governance layer.")
    _note("No state mutations occurred. Escalation was logged to the audit trail.")


# ============================================================
# Scenario BM — CLI Workflow Interaction (Approve path)
# ============================================================
async def scenario_bm() -> None:
    _section("Scenario BM — CLI Workflow Interaction (Approve Path)")

    state = _mk_state(budget_inr=40_000, nights=2)
    session = GuidanceSession(state=state, session_id="BM-cli-01")

    _freya_says(
        "Meal budget selection pending approval. "
        "Proposed plan: ₹2,200/day × 2 days = ₹4,400."
    )
    _note("Simulating: user reads the prompt and selects [1] Approve.")
    _user_says("[1]")

    outcome, result = await session.run_checkpoint(
        context="Meal Budget Selection",
        reason="Meal plan at ₹2,200/day is within budget but above standard ₹1,800/day benchmark.",
        recommendation="Approve ₹2,200/day meal allowance for 2-day trip.",
        sim_choice="approve",
    )

    print(f"\n  Outcome: {_BOLD}{outcome}{_RESET}")
    print(render_guidance_result(result))
    _note("Workflow continues. Approval checkpoint cleared.")


# ============================================================
# Scenario BN — Guidance Audit Trail
# ============================================================
async def scenario_bn() -> None:
    _section("Scenario BN — Guidance Audit Trail")

    state = _mk_state(budget_inr=60_000, nights=3)
    trail = GuidanceAuditTrail(session_id="BN-audit-trail-01")
    session = GuidanceSession(state=state, session_id="BN-audit-trail-01")
    # Inject our shared trail reference
    session._trail = trail

    _freya_says("Running a multi-checkpoint session to build audit history…")

    # Event 1 — Approve
    await session.run_checkpoint(
        context="Flight Selection",
        reason="Business class selected — ₹18,000. Economy available at ₹7,200.",
        recommendation="Business class IndiGo flight.",
        sim_choice="approve",
    )

    # Event 2 — Guidance: cost reduction
    _user_says("Something cheaper for the hotel — ₹6,000/night is fine.")
    await session.run_checkpoint(
        context="Hotel Selection",
        reason="Current hotel at ₹11,000/night exceeds sub-budget.",
        recommendation="Courtyard by Marriott — ₹11,000/night.",
        sim_choice="guidance",
        sim_guidance_text="Something cheaper for the hotel — ₹6,000 per night is fine.",
    )

    # Event 3 — Guidance: priority change
    _user_says("Prioritise speed — I have early meetings.")
    await session.run_checkpoint(
        context="Ground Transport",
        reason="Multiple transport options available.",
        recommendation="Metro + auto — ₹450, 55 min.",
        sim_choice="guidance",
        sim_guidance_text="Prioritise speed — I have early meetings.",
    )

    # Event 4 — Reject
    await session.run_checkpoint(
        context="Optional Add-ons",
        reason="Travel insurance ₹1,800 proposed.",
        recommendation="Add travel insurance to plan.",
        sim_choice="reject",
    )

    _freya_says("Session complete. Full guidance audit trail:")
    print()
    print(trail.render())


# ============================================================
# Main
# ============================================================
async def main() -> None:
    print(f"\n{_BOLD}{'═' * 70}")
    print("  Freya — Advanced HITL: Human Operational Guidance Demo")
    print(f"{'═' * 70}{_RESET}")

    await scenario_bi()
    await scenario_bj()
    await scenario_bk()
    await scenario_bl()
    await scenario_bm()
    await scenario_bn()

    print()
    print(f"{_CYAN}{'═' * 70}{_RESET}")
    print(f"{_GREEN}{_BOLD}  All HITL guidance scenarios complete.{_RESET}")
    print(f"{_CYAN}{'═' * 70}{_RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
