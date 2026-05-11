"""freya/negotiation/degradation.py

GracefulOperationalDegradationEngine

Safely reduces workflow operational quality when under resource pressure.

Design rules:
  - Always preserves a minimum quality floor per workflow
  - Degradation is always reversible
  - Critical workflows cannot degrade below safety floor
  - Governance guarantees are never traded away
  - Recovery is automatic when pressure normalizes
"""
from __future__ import annotations

from freya.negotiation.models import DegradationMode, WorkflowDegradationPlan

_CRITICALITY_FLOORS: dict[str, float] = {
    "critical":   0.85,
    "high":       0.70,
    "standard":   0.55,
    "low":        0.35,
    "background": 0.20,
}

_MODE_CAPABILITIES: dict[DegradationMode, list[str]] = {
    "reduced_reasoning":    ["deep analysis", "multi-step reasoning", "sub-agent delegation"],
    "lightweight_planning": ["iterative planning", "full DAG traversal", "complex constraint checking"],
    "skip_optimization":    ["cost optimization passes", "quality tuning passes", "preference re-ranking"],
    "compressed_analysis":  ["detailed reporting", "full audit logging", "comprehensive validation"],
    "deferred_retries":     ["automatic retries", "fallback execution paths"],
    "governance_batching":  ["on-demand governance reviews", "real-time approval prompts"],
    "none":                 [],
}

_MODE_QUALITY_REDUCTION: dict[DegradationMode, float] = {
    "reduced_reasoning":    0.20,
    "lightweight_planning": 0.25,
    "skip_optimization":    0.15,
    "compressed_analysis":  0.18,
    "deferred_retries":     0.10,
    "governance_batching":  0.08,
    "none":                 0.00,
}

_MODE_QUALITY_IMPACT: dict[DegradationMode, str] = {
    "reduced_reasoning":    "Shallower analysis; multi-step reasoning replaced by heuristics.",
    "lightweight_planning": "Faster but less-optimal plans; complex constraints approximated.",
    "skip_optimization":    "Execution proceeds without quality-optimization passes.",
    "compressed_analysis":  "Condensed reporting; detailed audit trail deferred.",
    "deferred_retries":     "Fewer retry attempts; transient failures may surface.",
    "governance_batching":  "Governance reviews batched; slight latency increase for approvals.",
    "none":                 "No quality reduction.",
}


class GracefulOperationalDegradationEngine:
    """Plans and validates bounded, reversible workflow degradation."""

    def plan(
        self,
        workflow_id: str,
        criticality: str,
        current_pressure: float,
        current_quality: float = 1.0,
    ) -> WorkflowDegradationPlan:
        """Return an appropriate degradation plan for current pressure."""
        mode  = self._select_mode(criticality, current_pressure)
        floor = _CRITICALITY_FLOORS.get(criticality, 0.50)

        # Safety check: never degrade below floor
        quality_after = current_quality - _MODE_QUALITY_REDUCTION.get(mode, 0.0)
        if quality_after < floor:
            # Soften to next-least-invasive mode
            mode = self._soften(mode)
            quality_after = current_quality - _MODE_QUALITY_REDUCTION.get(mode, 0.0)
            quality_after = max(quality_after, floor)

        return WorkflowDegradationPlan(
            workflow_id=workflow_id,
            degradation_mode=mode,
            reduced_capabilities=list(_MODE_CAPABILITIES.get(mode, [])),
            expected_quality_impact=_MODE_QUALITY_IMPACT.get(mode, "Unknown."),
            reversibility=True,
            recovery_trigger="resource_pressure_below_0.55",
            minimum_quality_floor=floor,
        )

    def is_safe(
        self,
        plan: WorkflowDegradationPlan,
        current_quality: float,
        criticality: str,
    ) -> bool:
        """Validate that a degradation plan does not violate the quality floor."""
        reduction = _MODE_QUALITY_REDUCTION.get(plan.degradation_mode, 0.0)
        floor     = _CRITICALITY_FLOORS.get(criticality, 0.50)
        return (current_quality - reduction) >= floor

    def recovery_plan(self, degraded: WorkflowDegradationPlan) -> WorkflowDegradationPlan:
        """Return the restored (no-degradation) version of a plan."""
        return WorkflowDegradationPlan(
            workflow_id=degraded.workflow_id,
            degradation_mode="none",
            reduced_capabilities=[],
            expected_quality_impact="Full operational quality restored.",
            reversibility=True,
            recovery_trigger="manual",
            minimum_quality_floor=degraded.minimum_quality_floor,
        )

    def describe(self, plan: WorkflowDegradationPlan) -> list[str]:
        lines = [
            f"Workflow:    {plan.workflow_id}",
            f"Mode:        {plan.degradation_mode.replace('_', ' ').title()}",
            f"Impact:      {plan.expected_quality_impact}",
            f"Reversible:  {'Yes' if plan.reversibility else 'No'}",
            f"Recovery:    {plan.recovery_trigger}",
        ]
        if plan.reduced_capabilities:
            lines.append("Suspended:   " + ", ".join(plan.reduced_capabilities))
        return lines

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _select_mode(criticality: str, pressure: float) -> DegradationMode:
        if criticality in ("critical", "high"):
            # Only allow the least invasive modes
            if pressure >= 0.90:
                return "governance_batching"
            return "none"
        if pressure >= 0.92:
            return "lightweight_planning"
        if pressure >= 0.82:
            return "reduced_reasoning"
        if pressure >= 0.72:
            return "skip_optimization"
        if pressure >= 0.62:
            return "compressed_analysis"
        if pressure >= 0.52:
            return "deferred_retries"
        return "none"

    @staticmethod
    def _soften(mode: DegradationMode) -> DegradationMode:
        """Return the next-less-invasive degradation mode."""
        order: list[DegradationMode] = [
            "lightweight_planning",
            "reduced_reasoning",
            "skip_optimization",
            "compressed_analysis",
            "deferred_retries",
            "governance_batching",
            "none",
        ]
        idx = order.index(mode) if mode in order else 0
        return order[min(idx + 1, len(order) - 1)]
