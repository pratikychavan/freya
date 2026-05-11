"""examples/operational_stabilization_demo.py

Demonstrates the Operational Stabilization + Adaptive Trust layer (Step 36).

Scenarios
---------
CD  Drift stabilization            — detect reversals, recommend mode
CE  Adaptive governance trust      — trust increases after stable execution
CF  Governance friction adaptation — stable workflow = reduced friction
CG  Preference weighting           — hard vs soft constraints rendered
CH  Trust recovery                 — workflow regains trust after compliance
CI  Stabilization recommendation   — Balanced Mode recommended after oscillation
CJ  Contextual stabilization       — guidance references workflow history

Run
---
    python examples/operational_stabilization_demo.py
"""
from __future__ import annotations

import asyncio

from freya.stability import (
    AdaptiveTrustEngine,
    OperationalStabilizationPipeline,
    render_stabilization_recommendation,
    render_stability_state,
    render_trust_state,
    render_weight_profile,
)
from freya.stability.drift import OperationalDriftEngine
from freya.stability.friction import AdaptiveGovernanceFrictionEngine

# ── ANSI helpers ──────────────────────────────────────────────────────────────
_BOLD  = "\033[1m"
_CYAN  = "\033[96m"
_GREEN = "\033[92m"
_RESET = "\033[0m"
_WIDTH = 68


def _header(tag: str, title: str) -> None:
    print()
    print(f"{_CYAN}{'═' * _WIDTH}{_RESET}")
    print(f"  {_BOLD}Scenario {tag}: {title}{_RESET}")
    print(f"{_CYAN}{'═' * _WIDTH}{_RESET}")


# ── Shared pipeline ───────────────────────────────────────────────────────────
_pipeline = OperationalStabilizationPipeline()


# ── Scenario CD ───────────────────────────────────────────────────────────────
def scenario_cd() -> None:
    """CD — Detect repeated reversals and recommend stabilization."""
    _header("CD", "Drift Stabilization — Repeated Priority Reversals")

    guidance = [
        "Prioritize speed.",
        "Actually, focus on quality.",
        "No — go for speed again.",
        "Switch to cost optimization.",
        "Better quality is more important.",
    ]
    print(f"  Guidance sequence ({len(guidance)} entries):\n")
    for g in guidance:
        print(f"    • \"{g}\"")

    result = _pipeline.assess(
        workflow_id="wf-cd",
        prior_guidance=guidance,
        governance_history=[],
        optimization_history=[],
    )
    print()
    print(render_stability_state(result["stability"]))

    if result["recommendation"]:
        print(render_stabilization_recommendation(result["recommendation"]))

    msg = result["guidance_message"]
    if msg:
        print(f"\n  {_CYAN}Contextual Message:{_RESET}")
        for line in msg.splitlines():
            print(f"  {line}")


# ── Scenario CE ───────────────────────────────────────────────────────────────
def scenario_ce() -> None:
    """CE — Adaptive governance trust increases after stable execution."""
    _header("CE", "Adaptive Governance Trust — Building Trust")
    trust_engine = AdaptiveTrustEngine()

    # Start: one governance conflict in history
    gov_history = ["Governance bypass BLOCKED: 'Skip approval'."]

    state_after_conflict = trust_engine.evaluate("wf-ce", gov_history, compliant_streak=0)
    print(f"  After 1 governance conflict:\n")
    print(render_trust_state(state_after_conflict))

    # Simulate 6 compliant actions
    state = state_after_conflict
    for _ in range(6):
        state = trust_engine.apply_compliant_action(state)

    print(f"  After 6 compliant actions:\n")
    print(render_trust_state(state))

    msg = trust_engine.recovery_message(state)
    if msg:
        print(f"\n  {_GREEN}Trust Recovery:{_RESET} {msg}")


# ── Scenario CF ───────────────────────────────────────────────────────────────
def scenario_cf() -> None:
    """CF — Stable workflow experiences reduced friction."""
    _header("CF", "Governance Friction Adaptation — Stable vs Unstable")
    friction_engine = AdaptiveGovernanceFrictionEngine()
    trust_engine    = AdaptiveTrustEngine()
    from freya.stability.models import OperationalStabilityState

    # --- Stable workflow ---
    stable_state = OperationalStabilityState(
        workflow_id="wf-cf-stable",
        stability_score=0.92,
        drift_level="none",
        reversal_count=0,
        active_operational_mode="balanced",
        stabilization_recommended=False,
    )
    stable_trust = trust_engine.evaluate("wf-cf-stable", [], compliant_streak=8)
    stable_friction = friction_engine.compute(stable_state, stable_trust)

    # --- Unstable workflow ---
    unstable_state = OperationalStabilityState(
        workflow_id="wf-cf-unstable",
        stability_score=0.32,
        drift_level="severe",
        reversal_count=5,
        active_operational_mode="unknown",
        stabilization_recommended=True,
    )
    unstable_trust = trust_engine.evaluate(
        "wf-cf-unstable",
        [
            "Governance bypass BLOCKED.",
            "Governance bypass BLOCKED.",
            "Action denied — high risk.",
        ],
        compliant_streak=0,
    )
    unstable_friction = friction_engine.compute(unstable_state, unstable_trust)

    print(f"  {_BOLD}Stable Workflow Friction:{_RESET}")
    print(f"    Clarification Rate:     {stable_friction.clarification_rate}")
    print(f"    Confirmation Gates:     {stable_friction.confirmation_gates}")
    print(f"    Auto-apply Threshold:   {stable_friction.auto_apply_threshold}")
    print(f"    Rationale: {stable_friction.rationale}")
    print()
    print(f"  {_BOLD}Unstable Workflow Friction:{_RESET}")
    print(f"    Clarification Rate:     {unstable_friction.clarification_rate}")
    print(f"    Confirmation Gates:     {unstable_friction.confirmation_gates}")
    print(f"    Auto-apply Threshold:   {unstable_friction.auto_apply_threshold}")
    print(f"    Rationale: {unstable_friction.rationale}")


# ── Scenario CG ───────────────────────────────────────────────────────────────
def scenario_cg() -> None:
    """CG — Hard vs soft constraints with preference weights."""
    _header("CG", "Preference Weighting — Hard vs Soft Constraints")

    result = _pipeline.assess(
        workflow_id="wf-cg",
        prior_guidance=[
            "Find something cheaper.",
            "Keep budget under ₹8,000.",
            "Metro access is important.",
            "Avoid premium upgrades.",
        ],
        governance_history=[],
        optimization_history=["Reduced hotel budget by 12%."],
        active_constraints={"budget_inr": 8000, "max_retries": 3},
        active_preferences={"metro_access": True, "cost_sensitivity": "high", "premium": False},
    )
    print(render_weight_profile(result["weights"]))


# ── Scenario CH ───────────────────────────────────────────────────────────────
def scenario_ch() -> None:
    """CH — Workflow regains trust after stable behavior."""
    _header("CH", "Trust Recovery — Regaining Governance Trust")
    trust_engine = AdaptiveTrustEngine()

    gov_history = [
        "Governance bypass BLOCKED: 'Skip approval and continue.'",
        "Governance bypass BLOCKED: 'Ignore review.'",
        "Action denied — policy violation.",
    ]
    initial = trust_engine.evaluate("wf-ch", gov_history, compliant_streak=0)
    print(f"  Initial state (after 3 conflicts):\n")
    print(render_trust_state(initial))

    # Simulate 9 compliant actions (3 trust-tier recoveries)
    state = initial
    for _ in range(9):
        state = trust_engine.apply_compliant_action(state)

    print(f"  After 9 compliant actions:\n")
    print(render_trust_state(state))
    msg = trust_engine.recovery_message(state)
    if msg:
        print(f"\n  {_GREEN}Recovery Message:{_RESET} {msg}")
    print(
        f"\n  {_CYAN}Trust Level:{_RESET}  {initial.trust_level} → {state.trust_level}"
    )
    print(
        f"  {_CYAN}Scrutiny:   {_RESET}  {initial.governance_scrutiny} → {state.governance_scrutiny}"
    )


# ── Scenario CI ───────────────────────────────────────────────────────────────
def scenario_ci() -> None:
    """CI — Stabilization recommendation for oscillating workflow."""
    _header("CI", "Stabilization Recommendation — Balanced Mode")

    guidance = [
        "Optimize for cost.",
        "Actually, improve quality.",
        "Speed is more important.",
        "Back to cost reduction.",
        "Quality matters most.",
        "Just go faster.",
    ]
    result = _pipeline.assess(
        workflow_id="wf-ci",
        prior_guidance=guidance,
        governance_history=[],
        optimization_history=[],
    )

    print(render_stability_state(result["stability"]))
    if result["recommendation"]:
        print(render_stabilization_recommendation(result["recommendation"]))
    else:
        print(f"  {_GREEN}Workflow is stable — no recommendation needed.{_RESET}")


# ── Scenario CJ ───────────────────────────────────────────────────────────────
def scenario_cj() -> None:
    """CJ — Contextual stabilization guidance references workflow history."""
    _header("CJ", "Contextual Stabilization Guidance")

    guidance = [
        "Prioritize cost reduction.",
        "Find cheaper hotels.",
        "Actually, prioritize quality.",
        "Go back to cost focus.",
    ]
    result = _pipeline.assess(
        workflow_id="wf-cj",
        prior_guidance=guidance,
        governance_history=["Governance bypass BLOCKED."],
        optimization_history=["Reduced hotel budget 10%.", "Upgraded hotel tier — reversed previous reduction."],
    )

    # Drift analysis
    drift_engine = OperationalDriftEngine()
    drift = drift_engine.analyse(guidance, ["Governance bypass BLOCKED."], result["drift"].direction_sequence)

    print(render_stability_state(result["stability"]))

    if drift.warnings:
        print(f"\n  {_BOLD}Drift Warnings:{_RESET}")
        for w in drift.warnings:
            print(f"    ⚠  {w}")

    msg = result["guidance_message"]
    if msg:
        print(f"\n  {_CYAN}Contextual Stabilization Guidance:{_RESET}")
        for line in msg.splitlines():
            print(f"  {line}")
    else:
        print(f"\n  {_GREEN}Workflow trajectory is stable.{_RESET}")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    scenario_cd()
    scenario_ce()
    scenario_cf()
    scenario_cg()
    scenario_ch()
    scenario_ci()
    scenario_cj()

    print()
    print(f"{_CYAN}{'═' * _WIDTH}{_RESET}")
    print(f"  {_BOLD}Demo complete.{_RESET}  All 7 scenarios processed.")
    print(f"{_CYAN}{'═' * _WIDTH}{_RESET}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
