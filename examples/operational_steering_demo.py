"""examples/operational_steering_demo.py

Constraint Negotiation + Operational Steering — Demo
=====================================================

Scenarios:
  AV — Budget vs Convenience Negotiation : detect conflict, show options
  AW — Runtime Steering                  : user changes priority mid-workflow
  AX — Recommendation Engine             : proactive optimization suggestion
  AY — Preference Memory                 : system remembers prior tendencies
  AZ — Economics + Steering Integration  : steering changes execution economics
  BA — Governance-Aware Steering         : steering triggers governance review

Run with:
    python examples/operational_steering_demo.py
"""
from __future__ import annotations

from freya.steering import (
    OperationalRecommendationEngine,
    PreferenceMemory,
    SteeringCoordinator,
    render_negotiation,
    render_operational_update,
    render_recommendation,
    render_recommendations,
    render_steering_state,
)
from freya.steering.models import SteeringDecision

# ── ANSI helpers ─────────────────────────────────────────────────────
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RESET = "\033[0m"


def _section(label: str) -> None:
    width = 70
    print()
    print(f"{_CYAN}{'═' * width}{_RESET}")
    print(f"{_BOLD}  {label}{_RESET}")
    print(f"{_CYAN}{'═' * width}{_RESET}")


def _user_says(text: str) -> None:
    print(f"\n  {_DIM}User:{_RESET} {_YELLOW}\"{text}\"{_RESET}\n")


def _freya_says(text: str) -> None:
    print(f"\n  {_DIM}Freya:{_RESET} {text}\n")


# ---------------------------------------------------------------------------
# Scenario AV — Budget vs Convenience Negotiation
# ---------------------------------------------------------------------------
def scenario_av() -> None:
    _section("Scenario AV — Budget vs Convenience Negotiation")

    _user_says("Plan my Bangalore trip, 2 nights, ₹40,000 budget. I need a hotel near the venue.")

    coordinator = SteeringCoordinator()
    state = SteeringCoordinator.build_state(
        goal="Plan Bangalore business trip",
        budget_inr=40_000,
        nights=2,
        preferences=["hotel_proximity"],
        strategy="hybrid",
    )

    proposals = coordinator.negotiate(state)

    if not proposals:
        print("  No conflicts detected.")
        return

    for proposal in proposals:
        print(render_negotiation(proposal))

    # Simulate user chooses option 1 — increase budget
    _user_says("Option 1 — I'll increase the budget.")
    decision = coordinator.apply_choice(state, proposals[0], "increase_budget")
    print(render_operational_update(decision))
    print(render_steering_state(state))


# ---------------------------------------------------------------------------
# Scenario AW — Runtime Steering
# ---------------------------------------------------------------------------
def scenario_aw() -> None:
    _section("Scenario AW — Runtime Steering: Priority Change Mid-Workflow")

    coordinator = SteeringCoordinator()
    state = SteeringCoordinator.build_state(
        goal="Plan Delhi leadership summit trip",
        budget_inr=60_000,
        nights=3,
        preferences=["premium", "hotel_proximity"],
        strategy="cognitive",
    )

    _freya_says("I've synthesised your workflow. Planning is underway.")
    print(render_steering_state(state))

    _user_says("Actually, bring costs down. Don't need premium options.")
    decision = coordinator.steer(state, "cost")
    print(render_operational_update(decision))

    print(f"\n  {_DIM}Updated operational state:{_RESET}")
    print(render_steering_state(state))

    # Show economics impact after steering
    econ = coordinator.economics_impact(state)
    print(f"\n  {_BOLD}Economics impact{_RESET}")
    for k, v in econ.items():
        label = k.replace("_", " ").title()
        print(f"    • {label}: {v}")


# ---------------------------------------------------------------------------
# Scenario AX — Recommendation Engine
# ---------------------------------------------------------------------------
def scenario_ax() -> None:
    _section("Scenario AX — Proactive Recommendation Engine")

    coordinator = SteeringCoordinator()
    state = SteeringCoordinator.build_state(
        goal="Plan Mumbai client visit",
        budget_inr=55_000,
        nights=2,
        preferences=["hotel_proximity", "speed"],
        strategy="hybrid",
    )

    _freya_says("No major conflicts detected. Here are some ways to optimise your trip:")

    recs = coordinator.recommend(state)
    if recs:
        print(render_recommendations(recs))
    else:
        print("  No recommendations available.")

    # User acts on the top recommendation
    if recs:
        top = recs[0]
        _user_says(f"Good idea — go ahead with: {top.suggested_action}")
        print(f"  {_GREEN}✓ Applied: {top.headline}{_RESET}")


# ---------------------------------------------------------------------------
# Scenario AY — Preference Memory
# ---------------------------------------------------------------------------
def scenario_ay() -> None:
    _section("Scenario AY — Preference Memory")

    # Simulate three past decisions in separate sessions
    memory = PreferenceMemory(persist_path=None)  # in-memory only for demo

    # Session 1
    memory.record_decision(SteeringDecision(
        proposal_id="s1", chosen_option_id="economy_flight",
        applied_updates={"flight_class": "economy"},
        narrative="Booked economy class to save costs."
    ))
    # Session 2
    memory.record_decision(SteeringDecision(
        proposal_id="s2", chosen_option_id="stay_farther",
        applied_updates={"hotel_proximity": False},
        narrative="Accepted farther hotel to save ₹4,000."
    ))
    # Session 3
    memory.record_decision(SteeringDecision(
        proposal_id="s3", chosen_option_id="economy_flight",
        applied_updates={"flight_class": "economy"},
        narrative="Booked economy again."
    ))

    _freya_says("Based on your past trips, I've detected these tendencies:")
    summary = memory.tendency_summary()
    for label, tendency in summary.items():
        print(f"    • {label}: {tendency}")

    # New trip — coordinator uses memory to pre-populate preferences
    coordinator = SteeringCoordinator(memory=memory)
    state = SteeringCoordinator.build_state(
        goal="Plan Pune client visit",
        budget_inr=30_000,
        nights=2,
    )

    # Pre-load known preferences from memory
    for pref in memory.all_preferences():
        state.preferences.append(pref)

    proposals = coordinator.negotiate(state)
    if proposals:
        print()
        _freya_says("Based on your preference for lower cost, I'll pre-select the economical option:")
        print(render_negotiation(proposals[0]))
    else:
        print(f"\n  {_GREEN}✓ No conflicts — preferences from memory kept planning on track.{_RESET}")


# ---------------------------------------------------------------------------
# Scenario AZ — Economics + Steering Integration
# ---------------------------------------------------------------------------
def scenario_az() -> None:
    _section("Scenario AZ — Economics + Steering Integration")

    coordinator = SteeringCoordinator()
    state = SteeringCoordinator.build_state(
        goal="Plan Hyderabad tech conference trip",
        budget_inr=80_000,
        nights=4,
        preferences=["premium"],
        strategy="cognitive",
        priority="quality",
    )

    print(f"  {_BOLD}Before steering:{_RESET}")
    econ_before = coordinator.economics_impact(state)
    for k, v in econ_before.items():
        print(f"    • {k.replace('_', ' ').title()}: {v}")
    gov_before = coordinator.governance_impact(state)
    print(f"    • Governance: {', '.join(gov_before) or 'none'}")

    _user_says("Stay within limits — lower cost please.")
    decision = coordinator.steer(state, "cost")
    print(render_operational_update(decision))

    print(f"  {_BOLD}After steering:{_RESET}")
    econ_after = coordinator.economics_impact(state)
    for k, v in econ_after.items():
        print(f"    • {k.replace('_', ' ').title()}: {v}")
    gov_after = coordinator.governance_impact(state)
    print(f"    • Governance: {', '.join(gov_after) or 'none'}")


# ---------------------------------------------------------------------------
# Scenario BA — Governance-Aware Steering
# ---------------------------------------------------------------------------
def scenario_ba() -> None:
    _section("Scenario BA — Governance-Aware Steering")

    coordinator = SteeringCoordinator()
    state = SteeringCoordinator.build_state(
        goal="Plan Singapore summit delegation",
        budget_inr=25_000,
        nights=2,
        preferences=["hotel_proximity"],
        strategy="deterministic",
    )

    gov_before = coordinator.governance_impact(state)
    print(f"  Governance before: {_GREEN}{', '.join(gov_before) or 'auto-approval eligible'}{_RESET}")

    _user_says("Actually, let's go premium — upgrade the budget to ₹90,000.")
    decision = coordinator.modify_constraint(state, "budget_inr", 90_000)
    print(render_operational_update(decision))

    gov_after = coordinator.governance_impact(state)
    print(f"  {_YELLOW}Governance after upgrade: {', '.join(gov_after)}{_RESET}")
    print()
    print(
        f"  {_YELLOW}⚑  High-value approval is now required before workflow can proceed.{_RESET}"
    )

    # Show full state
    print(render_steering_state(state))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"\n{_BOLD}{_CYAN}  Freya — Constraint Negotiation + Operational Steering{_RESET}")
    print(f"  {'─' * 52}")

    scenario_av()
    scenario_aw()
    scenario_ax()
    scenario_ay()
    scenario_az()
    scenario_ba()

    print(f"\n{_DIM}  Demo complete.{_RESET}\n")


if __name__ == "__main__":
    main()
