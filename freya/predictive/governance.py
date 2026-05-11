"""freya/predictive/governance.py

PredictiveGovernanceEngine

Forecasts governance overload and proactively coordinates approval batching.
Governance guarantees are always preserved — no requirement is permanently deferred.

Design rules:
  - Batching is bounded: max deferral window is configurable (default 20 min)
  - Pre-batching only occurs when confidence warrants action
  - Security and compliance approvals are never batched or delayed
  - Batching dissolves automatically when backlog clears
"""
from __future__ import annotations

from freya.predictive.models import (
    OperationalForecast,
    PredictiveAdjustmentPlan,
)
import uuid

# Approval categories that cannot be batched under any circumstances
_PROTECTED_APPROVAL_TYPES: frozenset[str] = frozenset({
    "security_escalation",
    "compliance_override",
    "data_access_critical",
    "incident_authorization",
})

_BATCH_WINDOW_MINUTES = 20  # Maximum deferral for batched reviews


class PredictiveGovernanceEngine:
    """Proactively coordinate governance approval capacity."""

    def assess_and_plan(
        self,
        forecast: OperationalForecast,
        pending_approvals: int,
        pending_approval_types: list[str] | None = None,
        current_approval_latency: float = 1.0,
        baseline_latency: float = 1.0,
    ) -> PredictiveAdjustmentPlan | None:
        """Return a proactive governance plan if warranted, else None."""
        if not forecast.action_warranted:
            return None  # Confidence too low for preemptive action

        governance_load = forecast.predicted_governance_load
        if governance_load in ("normal",) and pending_approvals < 4:
            return None  # No action needed

        adjustments: list[str] = []
        impact_parts: list[str] = []

        # Determine how aggressive to be based on governance load
        if governance_load in ("congested", "overloaded"):
            adjustments.append(
                "Low-priority approvals pre-batched into a scheduled review window."
            )
            adjustments.append(
                "Non-critical escalations deferred to next coordination cycle."
            )
            impact_parts.append("reduced escalation congestion")
            impact_parts.append("approval bandwidth preserved for priority workflows")

        elif governance_load in ("elevated", "increasing"):
            adjustments.append(
                "Approval queue monitored; minor reviews clustered to reduce interrupt frequency."
            )
            impact_parts.append("anticipated governance load smoothed")

        # Latency warning
        latency_ratio = current_approval_latency / max(baseline_latency, 0.01)
        if latency_ratio >= 1.5:
            adjustments.append(
                f"Approval latency trending {latency_ratio:.1f}× above baseline — "
                f"pre-routing non-critical reviews to asynchronous queue."
            )
            impact_parts.append("approval latency trend intercepted")

        # Never batch protected approval types
        if pending_approval_types:
            blocked = [t for t in pending_approval_types if t in _PROTECTED_APPROVAL_TYPES]
            if blocked:
                adjustments.append(
                    f"Protected approvals ({', '.join(blocked)}) exempt from batching — "
                    f"processed immediately."
                )

        if not adjustments:
            return None

        return PredictiveAdjustmentPlan(
            plan_id=str(uuid.uuid4())[:8],
            proactive_adjustments=adjustments,
            expected_prevention_impact=(
                "; ".join(impact_parts) if impact_parts else "governance load smoothed"
            ),
            governance_risk="none",
            reversibility=True,
            confidence_basis=forecast.confidence_score,
        )

    def should_batch(
        self,
        pending_approvals: int,
        governance_load: str,
        confidence: float,
    ) -> bool:
        if confidence < 0.50:
            return False
        if governance_load in ("normal",):
            return pending_approvals >= 6
        if governance_load in ("increasing", "elevated"):
            return pending_approvals >= 4
        return True  # congested / overloaded

    def max_deferral_window(self) -> int:
        return _BATCH_WINDOW_MINUTES
