"""freya/strategic_governance/forecasting.py

Strategic Continuity Forecasting Engine.

Anticipates governance saturation and continuity degradation across
forward-looking operational horizons. All forecasts are bounded,
operationally-grounded, and deterministic — not speculative AI predictions.
"""
from __future__ import annotations

from freya.strategic_governance.models import (
    OperationalContext,
    StrategicContinuityForecast,
)


# ---------------------------------------------------------------------------
# Context-horizon risk catalog
# Describes known organizational risk patterns for each operational context
# over short, medium, and long horizons.
# ---------------------------------------------------------------------------

_CONTEXT_RISKS: dict[str, dict] = {
    "normal": {
        "short":  [],
        "medium": ["gradual compression fatigue if usage continues unchanged"],
        "long":   ["portfolio monoculture drift if rotation is not actively managed"],
        "strategy": (
            "Maintain current balanced portfolio. Review reserve levels at cycle 4. "
            "No immediate intervention required."
        ),
    },
    "incident": {
        "short":  [
            "post-incident governance review surge (1–2 cycles post-resolution)",
            "retry amplification during governance recovery window",
        ],
        "medium": [
            "trust erosion if compression is sustained beyond incident resolution",
            "recovery responsiveness saturation from concurrent stabilization campaigns",
        ],
        "long":   ["governance review backlog compounding if post-incident review is deferred"],
        "strategy": (
            "Pre-position governance batch capacity for post-incident review surge. "
            "Gate compression removal on trust recovery metrics. "
            "Validate alternate recovery paths before incident resolution."
        ),
    },
    "audit": {
        "short":  [
            "governance review saturation from concurrent audit + routine traffic",
        ],
        "medium": [
            "escalation queue accumulation if review board capacity is not pre-expanded",
        ],
        "long":   ["governance rigidity drift if audit-mode restrictions persist beyond scope"],
        "strategy": (
            "Pre-expand review board capacity before audit window. "
            "Defer non-critical escalations. "
            "Define explicit audit scope end date to prevent governance rigidity lock-in."
        ),
    },
    "release_window": {
        "short":  [
            "recovery responsiveness pressure from release variance",
        ],
        "medium": [
            "governance review load spike during go/no-go decision windows",
            "resilience reserve depletion if multiple releases overlap",
        ],
        "long":   ["release fatigue compounding if release cadence acceleration continues"],
        "strategy": (
            "Stagger release windows to prevent concurrent governance strain. "
            "Pre-reserve recovery capacity before go/no-go decision points. "
            "Define release cadence limits to preserve review elasticity."
        ),
    },
    "migration": {
        "short":  [
            "recovery path brittleness during migration transition",
            "governance review surge for migration approvals",
        ],
        "medium": [
            "analytical trust degradation if compression is used to accelerate migration",
            "escalation saturation if migration blockers accumulate",
        ],
        "long":   ["post-migration governance debt if approvals were streamlined without audit trail"],
        "strategy": (
            "Maintain full governance review integrity during migration. "
            "Pre-position rollback capacity before each migration phase. "
            "Document all governance streamlining for post-migration audit."
        ),
    },
    "governance_review": {
        "short":  [
            "governance review cycle congestion from concurrent routine + review traffic",
        ],
        "medium": [
            "decision backlog if review scope expands mid-cycle",
        ],
        "long":   ["transparency erosion if review findings are not actioned within 2 cycles"],
        "strategy": (
            "Segregate governance review traffic from routine decision stream. "
            "Define maximum review scope at cycle start. "
            "Assign accountability owners to review findings within 2 cycles."
        ),
    },
}

_PROTECTED_CHARACTERISTICS_BY_CONTEXT: dict[str, list[str]] = {
    "normal":           ["governance_rigor", "analytical_trustworthiness", "operational_transparency"],
    "incident":         ["governance_rigor", "responsiveness", "recovery_quality"],
    "audit":            ["governance_rigor", "operational_transparency", "analytical_trustworthiness"],
    "release_window":   ["recovery_quality", "responsiveness", "operational_transparency"],
    "migration":        ["recovery_quality", "governance_rigor", "operational_transparency"],
    "governance_review":["governance_rigor", "analytical_trustworthiness", "operational_transparency"],
}


def _horizon_label(cycles: int) -> str:
    if cycles <= 2:
        return "short"
    if cycles <= 5:
        return "medium"
    return "long"


class StrategicContinuityForecastingEngine:
    """Forecasts organizational continuity risks for a given context and horizon."""

    def forecast(
        self,
        context: OperationalContext,
        horizon_cycles: int = 4,
        confidence: float = 0.70,
    ) -> StrategicContinuityForecast:
        """Return a StrategicContinuityForecast for the given context and horizon.

        Parameters
        ----------
        context:
            Current operational regime.
        horizon_cycles:
            Forward-looking cycle horizon (1–10).
        confidence:
            Analytical confidence [0.0, 1.0]. Low confidence limits forecast to
            short-horizon risks only.
        """
        profile = _CONTEXT_RISKS.get(context, _CONTEXT_RISKS["normal"])
        horizon = _horizon_label(horizon_cycles)

        # Collect risks up to confidence-adjusted horizon
        risks: list[str] = []
        include_horizons: list[str] = ["short"]
        if confidence >= 0.55:
            if horizon in ("medium", "long"):
                include_horizons.append("medium")
        if confidence >= 0.70:
            if horizon == "long":
                include_horizons.append("long")

        for h in include_horizons:
            risks.extend(profile.get(h, []))

        if not risks:
            risks = ["No significant continuity risks projected for this context and horizon."]

        strategy = profile["strategy"]
        if confidence < 0.55:
            strategy = (
                f"[LOW CONFIDENCE — short-horizon advisory only] {strategy}"
            )

        protected = _PROTECTED_CHARACTERISTICS_BY_CONTEXT.get(
            context, ["governance_rigor", "operational_transparency"]
        )

        return StrategicContinuityForecast(
            forecast_horizon=f"{horizon_cycles}-cycle {horizon} horizon ({context} context)",
            protected_operational_characteristics=protected,
            anticipated_risks=risks,
            continuity_strategy=strategy,
            confidence_score=round(confidence, 3),
        )
