"""freya/predictive/__init__.py

Predictive Operational Coordination Layer — public façade.

Quick start::

    from freya.predictive import PredictiveCoordinationPipeline

    pipeline = PredictiveCoordinationPipeline()
    result = pipeline.run(
        telemetry={
            "approval_latency":     2.5,
            "retry_rate":           0.12,
            "reasoning_pool_usage": 0.75,
        },
        pending_approvals=5,
        critical_workflows=["wf-incident"],
        background_workflows=["wf-analytics", "wf-reporting"],
        window_minutes=15,
    )
    print(result["report"])
"""
from __future__ import annotations

from freya.predictive.equilibrium import OperationalEquilibriumEngine
from freya.predictive.forecasting import OperationalForecastingEngine
from freya.predictive.governance import PredictiveGovernanceEngine
from freya.predictive.models import (
    EquilibriumAssessment,
    EquilibriumState,
    OperationalForecast,
    OperationalReservation,
    OperationalSignal,
    PredictiveAdjustmentPlan,
    RecoveryForecast,
    SmoothingPhase,
    StabilityTrend,
)
from freya.predictive.rendering import (
    render_equilibrium_state,
    render_full_predictive_state,
    render_operational_forecast,
    render_predictive_adjustments,
    render_recovery_forecast,
    render_reservation_state,
)
from freya.predictive.reservations import OperationalReservationEngine
from freya.predictive.signals import OperationalSignalEngine
from freya.predictive.smoothing import OperationalSmoothingEngine


class PredictiveCycleResult:
    """Structured result of one predictive coordination cycle."""

    def __init__(
        self,
        signals: list[OperationalSignal],
        forecast: OperationalForecast,
        equilibrium: EquilibriumAssessment,
        adjustment_plans: list[PredictiveAdjustmentPlan],
        reservations: list[OperationalReservation],
        recovery: RecoveryForecast | None,
    ) -> None:
        self.signals          = signals
        self.forecast         = forecast
        self.equilibrium      = equilibrium
        self.adjustment_plans = adjustment_plans
        self.reservations     = reservations
        self.recovery         = recovery


class PredictiveCoordinationPipeline:
    """High-level façade wiring all predictive coordination components.

    All components are deterministic and telemetry-driven.
    Confidence levels gate how aggressively preventive actions are applied.
    """

    def __init__(self) -> None:
        self._signals      = OperationalSignalEngine()
        self._forecasting  = OperationalForecastingEngine()
        self._equilibrium  = OperationalEquilibriumEngine()
        self._governance   = PredictiveGovernanceEngine()
        self._smoothing    = OperationalSmoothingEngine()
        self._reservations = OperationalReservationEngine()

    def run(
        self,
        telemetry: dict[str, float],
        pending_approvals: int = 0,
        critical_workflows: list[str] | None = None,
        background_workflows: list[str] | None = None,
        window_minutes: int = 15,
        current_pressure: float | None = None,
        stability_trend: str = "stable",
    ) -> dict:
        """Execute one predictive coordination cycle.

        Returns a dict with:
          - ``result``:  PredictiveCycleResult
          - ``report``:  human-readable string
          - ``action_warranted``: bool
          - ``stabilization_recommended``: bool
        """
        critical_workflows   = critical_workflows   or []
        background_workflows = background_workflows or []

        # 1. Read signals
        signals = self._signals.read(telemetry)

        # 2. Forecast
        forecast = self._forecasting.forecast(signals, window_minutes=window_minutes)

        # 3. Equilibrium
        equilibrium = self._equilibrium.assess(signals, forecast=forecast)

        # 4. Adjustment plans
        plans: list[PredictiveAdjustmentPlan] = []

        # Governance plan
        gov_plan = self._governance.assess_and_plan(
            forecast=forecast,
            pending_approvals=pending_approvals,
            current_approval_latency=telemetry.get("approval_latency", 1.0),
        )
        if gov_plan:
            plans.append(gov_plan)

        # Smoothing plan for background/low-priority workflows
        if background_workflows:
            smooth_plan = self._smoothing.plan(
                equilibrium=equilibrium,
                forecast=forecast,
                affected_workflows=background_workflows,
            )
            if smooth_plan:
                plans.append(smooth_plan)

        # 5. Reservations for critical workflows
        reservations: list[OperationalReservation] = []
        for wf in critical_workflows:
            reservation = self._reservations.reserve(
                resource="reasoning_capacity",
                protected_workflow=wf,
                reason=f"Predictive reservation: {forecast.predicted_pressure_level} pressure forecast.",
                forecast=forecast,
                base_fraction=0.25,
            )
            if reservation:
                reservations.append(reservation)

        # 6. Recovery forecast
        effective_pressure = current_pressure if current_pressure is not None else (
            self._signals.aggregate_pressure(signals)
        )
        recovery = self._forecasting.recovery_forecast(
            current_pressure=effective_pressure,
            active_signal_count=len(self._signals.rising_signals(signals)),
            trend=stability_trend,
        )

        # 7. Build report
        result = PredictiveCycleResult(
            signals=signals,
            forecast=forecast,
            equilibrium=equilibrium,
            adjustment_plans=plans,
            reservations=reservations,
            recovery=recovery,
        )
        report = render_full_predictive_state(
            forecast=forecast,
            equilibrium=equilibrium,
            adjustment_plans=plans,
            reservations=reservations,
            recovery=recovery,
        )

        return {
            "result":                   result,
            "report":                   report,
            "action_warranted":         forecast.action_warranted,
            "stabilization_recommended": equilibrium.stabilization_recommended,
        }

    def reservation_summary(self) -> dict[str, int]:
        return self._reservations.summary()

    def active_reservations(self) -> list[OperationalReservation]:
        return self._reservations.active_reservations()

    def release_reservations(self, workflow_id: str) -> list[OperationalReservation]:
        return self._reservations.release_for(workflow_id)


__all__ = [
    # Pipeline
    "PredictiveCoordinationPipeline",
    "PredictiveCycleResult",
    # Sub-engines
    "OperationalSignalEngine",
    "OperationalForecastingEngine",
    "OperationalEquilibriumEngine",
    "PredictiveGovernanceEngine",
    "OperationalSmoothingEngine",
    "OperationalReservationEngine",
    # Models
    "OperationalForecast",
    "EquilibriumAssessment",
    "OperationalReservation",
    "PredictiveAdjustmentPlan",
    "OperationalSignal",
    "RecoveryForecast",
    # Literals
    "EquilibriumState",
    "StabilityTrend",
    "SmoothingPhase",
    # Renderers
    "render_operational_forecast",
    "render_equilibrium_state",
    "render_predictive_adjustments",
    "render_reservation_state",
    "render_recovery_forecast",
    "render_full_predictive_state",
]
