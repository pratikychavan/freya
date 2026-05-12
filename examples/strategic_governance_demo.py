"""examples/strategic_governance_demo.py

Strategic Organizational Governance Cognition Layer — demonstration scenarios FC–FI.

These scenarios show how Freya coordinates strategic governance priorities,
forecasts elasticity thresholds, protects governance sustainability, and
applies oversight rules to strategic adaptation decisions.
"""
from __future__ import annotations

from freya.strategic_governance import StrategicGovernancePipeline
from freya.strategic_governance.elasticity import ResilienceElasticityCognitionEngine
from freya.strategic_governance.forecasting import StrategicContinuityForecastingEngine
from freya.strategic_governance.governance import StrategicGovernanceOversightEngine
from freya.strategic_governance.priorities import StrategicPriorityCoordinationEngine
from freya.strategic_governance.rendering import (
    render_elasticity_assessment,
    render_governance_sustainability,
    render_strategic_forecast,
    render_strategic_priorities,
)
from freya.strategic_governance.sustainability import GovernanceSustainabilityCognitionEngine


def _header(label: str, title: str) -> None:
    sep = "=" * 68
    print(f"\n{sep}")
    print(f"  {label}: {title}")
    print(sep)


# ---------------------------------------------------------------------------
# FC: Incident Priority Shift
# ---------------------------------------------------------------------------
def scenario_fc() -> None:
    _header("FC", "Incident Priority Shift — Responsiveness Prioritized Contextually")
    print(
        "Operational context: INCIDENT escalation window.\n"
        "Expected behavior: responsiveness + recovery quality elevated;\n"
        "optimization efficiency deprioritized; governance rigor preserved.\n"
    )
    engine = StrategicPriorityCoordinationEngine()
    priority = engine.prioritize("incident", confidence=0.75)
    print(render_strategic_priorities(priority))
    print(
        "\nInsight: Priority shift is contextual and temporary — governance rigor remains "
        "a hard constraint even during incidents. Analytical trustworthiness is deprioritized "
        "for speed but must be restored within 2 cycles of incident resolution."
    )


# ---------------------------------------------------------------------------
# FD: Governance Elasticity Warning
# ---------------------------------------------------------------------------
def scenario_fd() -> None:
    _header("FD", "Governance Elasticity Warning — Review Saturation Threshold Approaching")
    print(
        "Governance review queue is at 72% load.\n"
        "Elasticity threshold: 75%. Headroom is critically narrow.\n"
    )
    engine = ResilienceElasticityCognitionEngine()
    assessment = engine.assess("governance_review", current_load=0.72, confidence=0.70)
    print(render_elasticity_assessment(assessment))

    approaching = engine.approaching_threshold(assessment)
    print(f"\n  Approaching Threshold : {approaching}")
    print(
        "\nInsight: At 72% load against a 75% threshold, governance review responsiveness "
        "is within the 15% warning band. Preventive action is required NOW — not after "
        "the threshold is crossed. Reactive redistribution after saturation is far costlier."
    )


# ---------------------------------------------------------------------------
# FE: Audit-Window Governance Protection
# ---------------------------------------------------------------------------
def scenario_fe() -> None:
    _header("FE", "Audit-Window Governance Protection — Rigor Preserved Over Speed")
    print(
        "Operational context: AUDIT window.\n"
        "Expected behavior: governance rigor + transparency prioritized;\n"
        "responsiveness and optimization speed deprioritized.\n"
    )
    engine = StrategicPriorityCoordinationEngine()
    priority = engine.prioritize("audit", confidence=0.80)
    print(render_strategic_priorities(priority))

    # Verify governance guard: attempt to deprioritize governance rigor during audit
    governance = StrategicGovernanceOversightEngine()
    from freya.strategic_governance.models import StrategicGovernancePriority
    bad_priority = StrategicGovernancePriority(
        context_name="audit",
        prioritized_characteristics=["responsiveness"],
        temporarily_deprioritized=["governance_rigor", "operational_transparency"],
        governance_constraints=[],
        rationale="Speed-first audit approach.",
    )
    valid, violations = governance.validate_priority(bad_priority)
    print(f"\n  'Governance rigor deprioritized during audit' valid → {valid}")
    for v in violations:
        print(f"\n  {v}")
    print(
        "\nInsight: Governance rigor is unconditionally protected during audit windows. "
        "Any configuration attempting to deprioritize it is hard-blocked by the oversight engine."
    )


# ---------------------------------------------------------------------------
# FF: Strategic Continuity Forecast
# ---------------------------------------------------------------------------
def scenario_ff() -> None:
    _header("FF", "Strategic Continuity Forecast — Future Governance Overload Anticipated")
    print(
        "Operational context: INCIDENT (6-cycle medium horizon).\n"
        "Forecasting continuity risks across the recovery window.\n"
    )
    engine = StrategicContinuityForecastingEngine()
    forecast = engine.forecast("incident", horizon_cycles=6, confidence=0.72)
    print(render_strategic_forecast(forecast))
    print(
        "\nInsight: At a 6-cycle medium horizon, the forecast identifies both short-term "
        "(post-incident governance surge) and medium-term (trust erosion, responsiveness "
        "saturation) risks. The continuity strategy surfaces these proactively so "
        "governance capacity can be pre-positioned."
    )


# ---------------------------------------------------------------------------
# FG: Governance Sustainability Protection
# ---------------------------------------------------------------------------
def scenario_fg() -> None:
    _header("FG", "Governance Sustainability Protection — Review Redistribution Recommended")
    print(
        "Review load: 78% | Escalation load: 69%.\n"
        "Expected: saturated capacity state; redistribution recommended.\n"
    )
    engine = GovernanceSustainabilityCognitionEngine()
    state = engine.assess(review_load=0.78, escalation_load=0.69, confidence=0.70)
    print(render_governance_sustainability(state))
    print(
        "\nInsight: Combined review and escalation pressure has pushed governance capacity "
        "into a saturated state. The engine recommends batching lower-priority reviews and "
        "reserving escalation capacity before the critical threshold is crossed."
    )


# ---------------------------------------------------------------------------
# FH: Unsafe Strategic Tradeoff Blocked
# ---------------------------------------------------------------------------
def scenario_fh() -> None:
    _header("FH", "Unsafe Strategic Tradeoff Blocked — Trust Degradation Strategy Rejected")
    print(
        "Scenario: a configuration that deprioritizes analytical trustworthiness\n"
        "during a governance review period.\n"
        "Expected: governance oversight engine rejects this tradeoff.\n"
    )
    governance = StrategicGovernanceOversightEngine()
    from freya.strategic_governance.models import StrategicGovernancePriority
    bad_priority = StrategicGovernancePriority(
        context_name="governance_review",
        prioritized_characteristics=["responsiveness"],
        temporarily_deprioritized=["analytical_trustworthiness", "operational_transparency"],
        governance_constraints=[],
        rationale="Speed-optimized governance review.",
    )
    valid, violations = governance.validate_priority(bad_priority)
    print(f"  Priority valid → {valid}")
    for v in violations:
        print(f"\n  {v}")
    print(
        "\nInsight: Deprioritizing both analytical trustworthiness and operational "
        "transparency during a governance review period violates two core rules. "
        "The oversight engine blocks this configuration unconditionally — "
        "trust degradation strategies have no safe context."
    )


# ---------------------------------------------------------------------------
# FI: Executive Strategic Governance Summary — Full Pipeline
# ---------------------------------------------------------------------------
def scenario_fi() -> None:
    _header("FI", "Executive Strategic Governance Summary — Full Pipeline Run")
    print(
        "Running StrategicGovernancePipeline across a mixed operational state:\n"
        "  Context              : incident\n"
        "  Governance review    : 71% load  → approaching elasticity threshold\n"
        "  Analytical trust     : 65% load  → within tolerance\n"
        "  Escalation queue     : 63% load\n"
        "  Review load          : 71%\n"
        "  Horizon              : 5 cycles  | Confidence: 0.68\n"
    )
    pipeline = StrategicGovernancePipeline()
    result = pipeline.run(
        context="incident",
        domain_loads={
            "governance_review":      0.71,
            "analytical_trust":       0.65,
            "recovery_responsiveness": 0.55,
        },
        review_load=0.71,
        escalation_load=0.63,
        horizon_cycles=5,
        confidence=0.68,
    )
    print(result["render"])
    print(f"\n  Context          : {result['context'].upper()}")
    print(f"  Review Required  : {result['review_required']}")
    print(
        "\nInsight: The incident context correctly elevates responsiveness and recovery "
        "quality while preserving governance rigor as non-negotiable. Governance review "
        "elasticity approaching threshold triggers preventive action recommendations and "
        "the review_required flag, ensuring no escalation decisions proceed without "
        "governance oversight."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    scenario_fc()
    scenario_fd()
    scenario_fe()
    scenario_ff()
    scenario_fg()
    scenario_fh()
    scenario_fi()
    print("\n" + "=" * 68)
    print("  Strategic Organizational Governance Cognition — demo complete (FC–FI)")
    print("=" * 68 + "\n")
