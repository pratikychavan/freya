"""examples/organizational_resilience_demo.py

Organizational Resilience & Identity Cognition Layer — demonstration scenarios EV–FB.

These scenarios show how Freya preserves future adaptation capacity,
protects organizational operating characteristics, balances stabilization
portfolios, and applies governance guardrails to resilience decisions.
"""
from __future__ import annotations

from freya.resilience import OrganizationalResiliencePipeline
from freya.resilience.governance import ResilienceGovernanceEngine
from freya.resilience.identity import OrganizationalIdentityPreservationEngine
from freya.resilience.models import OperationalResilienceReserve
from freya.resilience.portfolio import AdaptationPortfolioBalancingEngine
from freya.resilience.rendering import (
    render_adaptation_portfolio,
    render_continuity_summary,
    render_identity_assessment,
    render_resilience_reserve,
)
from freya.resilience.reserves import OperationalResilienceReserveEngine


def _header(label: str, title: str) -> None:
    sep = "=" * 68
    print(f"\n{sep}")
    print(f"  {label}: {title}")
    print(sep)


# ---------------------------------------------------------------------------
# EV: Compression Reserve Depletion
# ---------------------------------------------------------------------------
def scenario_ev() -> None:
    _header("EV", "Compression Reserve Depletion — Future Capacity Warning")
    print(
        "Compression has been applied for 6 consecutive cycles.\n"
        "Reserve assessment: high depletion — future capacity is being exhausted.\n"
    )
    engine = OperationalResilienceReserveEngine()
    reserve = engine.assess_reserve("compression", usage_cycles=6, confidence=0.70)
    print(render_resilience_reserve(reserve))
    print(
        "\nInsight: At 6 cycles, compression reserve is at 30% capacity with HIGH depletion "
        "risk. Continued use risks exhausting the analytical trust reserve before the next "
        "high-severity event. Replenishment via batching rotation is required now."
    )


# ---------------------------------------------------------------------------
# EW: Organizational Identity Drift
# ---------------------------------------------------------------------------
def scenario_ew() -> None:
    _header("EW", "Organizational Identity Drift — Responsiveness Degradation Detected")
    print(
        "Active interventions:\n"
        "  batching:   6 cycles  → responsiveness degradation + governance throughput impairment\n"
        "  smoothing:  5 cycles  → accountability reduction\n"
    )
    identity_engine = OrganizationalIdentityPreservationEngine()
    profile = identity_engine.assess(
        active_interventions={"batching": 6, "smoothing": 5}
    )
    print(render_identity_assessment(profile))
    print(
        f"\nDrift detected: {identity_engine.has_drift(profile)}"
        f"\nPreservation priority: {profile.preservation_priority.upper()}"
        "\n\nInsight: Three protected characteristics are being actively degraded. "
        "'Responsiveness' and 'governance rigor' are at risk from sustained batching; "
        "'operational transparency' is being masked by prolonged smoothing. "
        "Identity preservation priority is ELEVATED — immediate rotation required."
    )


# ---------------------------------------------------------------------------
# EX: Strategic Adaptation Rotation
# ---------------------------------------------------------------------------
def scenario_ex() -> None:
    _header("EX", "Strategic Adaptation Rotation — Batching/Compression Portfolio Balanced")
    print(
        "Current portfolio:\n"
        "  compression:  7 cycles  (overused)\n"
        "  batching:     6 cycles  (overused)\n"
        "  smoothing:    2 cycles\n"
        "Assessing rotation balance and sustainability.\n"
    )
    portfolio_engine = AdaptationPortfolioBalancingEngine()
    portfolio = portfolio_engine.assess(
        active_strategies=["compression", "batching", "smoothing"],
        usage_counts={"compression": 7, "batching": 6, "smoothing": 2},
    )
    print(render_adaptation_portfolio(portfolio))
    recommendation = portfolio_engine.recommend_rotation(portfolio)
    print(f"\nRotation Recommendation:\n  {recommendation}")
    print(
        "\nInsight: Both compression and batching are overused, creating a skewed portfolio "
        "with sustainability score below 50%. Smoothing usage is healthy — it becomes the "
        "bridge while both primary strategies are rotated down."
    )


# ---------------------------------------------------------------------------
# EY: Continuity Preservation — Trust Maintained Under Stabilization
# ---------------------------------------------------------------------------
def scenario_ey() -> None:
    _header("EY", "Continuity Preservation — Operational Trust Maintained Under Pressure")
    print(
        "Active interventions:\n"
        "  compression:  3 cycles  (within tolerance)\n"
        "  batching:     3 cycles  (within tolerance)\n"
        "  smoothing:    2 cycles\n"
        "Confidence: 0.72 | All reserves within moderate risk band.\n"
    )
    pipeline = OrganizationalResiliencePipeline()
    result = pipeline.run(
        active_interventions={"compression": 3, "batching": 3, "smoothing": 2},
        confidence=0.72,
    )
    report = result["report"]
    print(render_identity_assessment(report.identity_profile))
    print()
    print(render_continuity_summary(report.continuity_assessment))
    print(
        f"\n  Continuity State : {result['continuity_state'].upper()}"
        f"\n  Review Required  : {result['review_required']}"
        "\n\nInsight: At moderate usage cycles, all five protected characteristics remain "
        "intact. No degradation signals are active — continuity is stable and trust is "
        "preserved without restricting current stabilization activity."
    )


# ---------------------------------------------------------------------------
# EZ: Unsafe Resilience Exhaustion Blocked
# ---------------------------------------------------------------------------
def scenario_ez() -> None:
    _header("EZ", "Unsafe Resilience Exhaustion Blocked — Chronic Compression Rejected")
    print(
        "Attempting to continue compression at 8 cycles.\n"
        "Governance rule: critical reserve depletion is hard-blocked.\n"
    )
    reserves_engine = OperationalResilienceReserveEngine()
    governance = ResilienceGovernanceEngine()

    reserve = reserves_engine.assess_reserve("compression", usage_cycles=8)
    print(render_resilience_reserve(reserve))

    valid, violations = governance.validate_reserve(reserve)
    print(f"\n  Reserve valid    → {valid}")
    for v in violations:
        print(f"\n  {v}")

    print(
        "\nInsight: At 8 cycles, compression reserve capacity is 10% — critical depletion. "
        "Governance unconditionally blocks further use. Analytical trust cannot be "
        "sacrificed for short-term stabilization gains. Replenishment is mandatory."
    )


# ---------------------------------------------------------------------------
# FA: Recovery Flexibility Preservation
# ---------------------------------------------------------------------------
def scenario_fa() -> None:
    _header("FA", "Recovery Flexibility Preservation — Future Reserve Protected")
    print(
        "Scenario: Conservative stabilization at early pressure stages.\n"
        "Active interventions: batching at 2 cycles, smoothing at 1 cycle.\n"
        "Goal: verify recovery flexibility reserves remain healthy.\n"
    )
    reserves_engine = OperationalResilienceReserveEngine()
    reserves = reserves_engine.assess_all(
        {"batching": 2, "smoothing": 1, "recovery_sequencing": 1},
        confidence=0.75,
    )
    for r in reserves:
        print(render_resilience_reserve(r))
        print()

    critical = reserves_engine.critical_reserves(reserves)
    overall = reserves_engine.overall_depletion_risk(reserves)
    print(f"  Overall Depletion Risk  : {overall.upper()}")
    print(f"  Critical Reserves       : {len(critical)}")
    print(
        "\nInsight: Early-stage conservative usage preserves all reserves above 80% capacity. "
        "Future recovery flexibility is fully intact — compression and governance reserves are "
        "available for high-severity events. This is the target steady-state posture."
    )


# ---------------------------------------------------------------------------
# FB: Executive Resilience Summary — Full Pipeline
# ---------------------------------------------------------------------------
def scenario_fb() -> None:
    _header("FB", "Executive Organizational Resilience Summary — Full Pipeline Run")
    print(
        "Running OrganizationalResiliencePipeline across a mixed usage landscape:\n"
        "  compression:         5 cycles  (high depletion risk)\n"
        "  batching:            6 cycles  (overused — responsiveness degradation)\n"
        "  smoothing:           5 cycles  (accountability reduction)\n"
        "  governance_review:   4 cycles  (moderate)\n"
        "Confidence: 0.65 | Assessing full resilience cognition state.\n"
    )
    pipeline = OrganizationalResiliencePipeline()
    result = pipeline.run(
        active_interventions={
            "compression": 5,
            "batching": 6,
            "smoothing": 5,
            "governance_review": 4,
        },
        confidence=0.65,
    )
    print(result["render"])
    print(f"\n  Continuity State : {result['continuity_state'].upper()}")
    print(f"  Review Required  : {result['review_required']}")
    print(
        "\nInsight: Sustained multi-intervention usage has degraded adaptation diversity "
        "and triggered identity preservation escalation. The pipeline surfaces governance "
        "violations, recommends rotation, and flags executive review — all before any "
        "further stabilization decisions are permitted."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    scenario_ev()
    scenario_ew()
    scenario_ex()
    scenario_ey()
    scenario_ez()
    scenario_fa()
    scenario_fb()
    print("\n" + "=" * 68)
    print("  Organizational Resilience & Identity Cognition — demo complete (EV–FB)")
    print("=" * 68 + "\n")
