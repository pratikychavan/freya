"""examples/proactive_optimization_demo.py

Proactive Operational Optimization — Demo
==========================================

Scenarios:
  BB — Cost Optimization              : proactive lower-cost hotel suggestion
  BC — Cognitive Spend Optimization   : reduce unnecessary reasoning depth
  BD — Delegation Optimization        : trim excessive child-workflow depth
  BE — Governance-Aware Optimization  : opportunity that requires approval
  BF — Continuous Reassessment        : state evolves, new opportunities emerge
  BG — Confidence-Aware Rendering     : strong vs weak confidence language
  BH — Economics + Optimization       : steering changes feed optimization

Run with:
    python examples/proactive_optimization_demo.py
"""
from __future__ import annotations

from freya.optimization import (
    OptimizationAdvisor,
    render_optimization_evaluation,
    render_optimization_proposal,
    render_optimization_summary,
)
from freya.steering import SteeringCoordinator
from freya.steering.models import OperationalConstraint, OperationalPreference

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


def _freya_says(text: str) -> None:
    print(f"\n  {_DIM}Freya:{_RESET} {text}\n")


def _user_says(text: str) -> None:
    print(f"\n  {_DIM}User:{_RESET} {_YELLOW}\"{text}\"{_RESET}\n")


# ---------------------------------------------------------------------------
# Scenario BB — Cost Optimization
# ---------------------------------------------------------------------------
def scenario_bb() -> None:
    _section("Scenario BB — Cost Optimization")

    _freya_says("Analysing workflow for cost optimizations…")

    state = SteeringCoordinator.build_state(
        goal="Plan Bangalore business trip",
        budget_inr=50_000,
        nights=3,
        strategy="hybrid",
    )
    # No proximity requirement → budget hotel alternative is viable
    advisor = OptimizationAdvisor()
    proposal = advisor.propose(state)

    if proposal:
        print(render_optimization_proposal(proposal))
        _user_says("Yes, apply the cost optimization.")
        top = proposal.opportunities[0]
        changes = advisor.apply_opportunity(state, top)
        print(f"  {_GREEN}✓ Applied changes:{_RESET}")
        for k, v in changes.items():
            print(f"    • {k.replace('_', ' ').title()}: {v}")
    else:
        print("  No cost optimizations available.")


# ---------------------------------------------------------------------------
# Scenario BC — Cognitive Spend Optimization
# ---------------------------------------------------------------------------
def scenario_bc() -> None:
    _section("Scenario BC — Cognitive Spend Optimization")

    _freya_says("Detected deep analysis mode on a low-complexity workflow…")

    state = SteeringCoordinator.build_state(
        goal="Plan quick Mumbai client call trip",
        budget_inr=15_000,
        nights=1,
        strategy="cognitive",
    )

    advisor = OptimizationAdvisor()
    proposal = advisor.propose(state)

    if proposal:
        print(render_optimization_proposal(proposal))
        _user_says("Switch to faster planning.")
        cog_opp = next(
            (o for o in proposal.opportunities if o.optimization_type == "cognitive"), None
        )
        if cog_opp:
            changes = advisor.apply_opportunity(state, cog_opp)
            print(f"  {_GREEN}✓ Strategy updated: {state.strategy}{_RESET}")
    else:
        print("  No cognitive optimization needed.")


# ---------------------------------------------------------------------------
# Scenario BD — Delegation Optimization
# ---------------------------------------------------------------------------
def scenario_bd() -> None:
    _section("Scenario BD — Delegation Depth Optimization")

    state = SteeringCoordinator.build_state(
        goal="Coordinate multi-city conference roadshow",
        budget_inr=80_000,
        nights=5,
    )
    # Simulate high delegation depth
    state.constraints["delegation_depth"] = OperationalConstraint(
        name="delegation_depth", value=7, negotiable=True
    )

    _freya_says("Detected excessive delegation depth — most layers add no value…")

    advisor = OptimizationAdvisor()
    proposal = advisor.propose(state)

    if proposal:
        print(render_optimization_proposal(proposal))
        del_opp = next(
            (o for o in proposal.opportunities if o.optimization_type == "delegation"), None
        )
        if del_opp:
            _user_says("Yes, reduce delegation layers.")
            changes = advisor.apply_opportunity(state, del_opp)
            new_depth = state.get_constraint("delegation_depth")
            print(f"  {_GREEN}✓ Delegation depth: {new_depth.value if new_depth else '?'}{_RESET}")
    else:
        print("  No delegation optimization needed.")


# ---------------------------------------------------------------------------
# Scenario BE — Governance-Aware Optimization
# ---------------------------------------------------------------------------
def scenario_be() -> None:
    _section("Scenario BE — Governance-Aware Optimization (Requires Approval)")

    state = SteeringCoordinator.build_state(
        goal="Plan Pune vendor review — low budget trip",
        budget_inr=22_000,
        nights=1,
    )
    # Simulate a manual approval requirement that may be removable
    state.constraints["require_manual_approval"] = OperationalConstraint(
        name="require_manual_approval", value=True, negotiable=True
    )

    _freya_says("Found an approval-streamlining opportunity — requires your sign-off…")

    advisor = OptimizationAdvisor()
    proposal = advisor.propose(state)

    if proposal:
        print(render_optimization_proposal(proposal))
        gov_opp = next(
            (o for o in proposal.opportunities if o.optimization_type == "governance"), None
        )
        if gov_opp:
            _user_says("I approve — remove the manual step.")
            try:
                # Must explicitly grant approval
                # apply_opportunity raises if it needs approval — caller confirms
                # We simulate "approved" by patching governance_impact temporarily
                gov_opp_approved = gov_opp.model_copy(
                    update={"governance_impact": "no_change"}
                )
                changes = advisor.apply_opportunity(state, gov_opp_approved)
                print(f"  {_GREEN}✓ Manual approval checkpoint removed.{_RESET}")
            except ValueError as e:
                print(f"  {_YELLOW}⚠ {e}{_RESET}")
    else:
        print("  No governance optimizations available.")


# ---------------------------------------------------------------------------
# Scenario BF — Continuous Optimization Reassessment
# ---------------------------------------------------------------------------
def scenario_bf() -> None:
    _section("Scenario BF — Continuous Optimization Reassessment")

    state = SteeringCoordinator.build_state(
        goal="Plan Chennai summit trip",
        budget_inr=60_000,
        nights=4,
        preferences=["premium"],
        strategy="cognitive",
    )

    advisor = OptimizationAdvisor()

    print(f"  {_DIM}[Phase 1 — initial state assessment]{_RESET}")
    eval_1 = advisor.evaluate(state)
    print(render_optimization_evaluation(eval_1))

    # Simulate mid-execution: user steered to cost mode
    coordinator = SteeringCoordinator()
    coordinator.steer(state, "cost")
    state.update_constraint("budget_inr", 35_000)

    print(f"  {_DIM}[Phase 2 — after user steered to 'cost' priority]{_RESET}")
    proposal = advisor.reassess(state)
    if proposal:
        print(render_optimization_proposal(proposal))
        _freya_says("New optimization opportunities emerged after priority change.")
    else:
        eval_2 = advisor.evaluate(state)
        print(render_optimization_evaluation(eval_2))
        _freya_says("No new significant opportunities after reassessment.")


# ---------------------------------------------------------------------------
# Scenario BG — Confidence-Aware Recommendations
# ---------------------------------------------------------------------------
def scenario_bg() -> None:
    _section("Scenario BG — Confidence-Aware Recommendations")

    # High-confidence scenario
    state_clear = SteeringCoordinator.build_state(
        goal="Plan Hyderabad client trip",
        budget_inr=45_000,
        nights=2,
        strategy="cognitive",
    )

    advisor = OptimizationAdvisor()
    proposal = advisor.propose(state_clear)

    if proposal and proposal.evaluation:
        ev = proposal.evaluation
        print(f"  {_BOLD}High-confidence case:{_RESET}")
        print(f"    Confidence: {ev.confidence_score:.0%}")
        print(f"    Language:   {ev.confidence_label()}")
        print(f"    Summary:    {render_optimization_summary(proposal)}")

    # Low-confidence scenario (few signals, minimal optimisation possible)
    state_vague = SteeringCoordinator.build_state(
        goal="Organise a meeting",
        budget_inr=8_000,
        nights=1,
        strategy="deterministic",
    )
    state_vague.constraints["delegation_depth"] = OperationalConstraint(
        name="delegation_depth", value=6, negotiable=True
    )

    proposal_low = advisor.propose(state_vague)
    if proposal_low and proposal_low.evaluation:
        ev = proposal_low.evaluation
        print(f"\n  {_BOLD}Lower-confidence case:{_RESET}")
        print(f"    Confidence: {ev.confidence_score:.0%}")
        print(f"    Language:   {ev.confidence_label()}")
        print(f"    Summary:    {render_optimization_summary(proposal_low)}")
    else:
        print(f"\n  {_DIM}No low-confidence case surfaced — state already optimal.{_RESET}")


# ---------------------------------------------------------------------------
# Scenario BH — Economics + Optimization Integration
# ---------------------------------------------------------------------------
def scenario_bh() -> None:
    _section("Scenario BH — Economics + Optimization Integration")

    coordinator = SteeringCoordinator()
    state = SteeringCoordinator.build_state(
        goal="Plan Kolkata partner summit trip",
        budget_inr=55_000,
        nights=3,
        strategy="cognitive",
        priority="quality",
    )

    advisor = OptimizationAdvisor()

    print(f"  {_BOLD}Economics before optimization:{_RESET}")
    econ_before = coordinator.economics_impact(state)
    for k, v in econ_before.items():
        print(f"    • {k.replace('_', ' ').title()}: {v}")

    proposal = advisor.propose(state)
    if proposal:
        print()
        print(render_optimization_proposal(proposal))

        # Apply all allowed opportunities
        applied_count = 0
        for opp in proposal.opportunities:
            try:
                advisor.apply_opportunity(state, opp)
                applied_count += 1
            except ValueError:
                pass   # needs approval — skip in this scenario

        if applied_count:
            print(f"  {_GREEN}✓ {applied_count} optimization(s) applied.{_RESET}")
            print(f"\n  {_BOLD}Economics after optimization:{_RESET}")
            econ_after = coordinator.economics_impact(state)
            for k, v in econ_after.items():
                print(f"    • {k.replace('_', ' ').title()}: {v}")

            # Show updated eval
            eval_after = advisor.evaluate(state)
            print()
            print(render_optimization_evaluation(eval_after))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"\n{_BOLD}{_CYAN}  Freya — Proactive Operational Optimization{_RESET}")
    print(f"  {'─' * 45}")

    scenario_bb()
    scenario_bc()
    scenario_bd()
    scenario_be()
    scenario_bf()
    scenario_bg()
    scenario_bh()

    print(f"\n{_DIM}  Demo complete.{_RESET}\n")


if __name__ == "__main__":
    main()
