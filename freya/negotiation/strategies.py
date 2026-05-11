"""freya/negotiation/strategies.py

NegotiationStrategyEngine

Generates the least-disruptive negotiation strategy for a given pressure
scenario. Deterministic-first; always explainable.

Supported strategies:
  temporary_degradation   — reduce reasoning/quality temporarily
  reasoning_compression   — switch to shallower reasoning mode
  optimization_deferral   — delay non-critical optimization cycles
  staged_execution        — break execution into progressive passes
  elastic_reallocation    — shift capacity from low to high priority
  governance_batching     — batch governance reviews to reduce interrupts
  no_action               — situation stable; no strategy needed
"""
from __future__ import annotations

from freya.negotiation.models import (
    DegradationMode,
    NegotiationProposal,
    NegotiationStrategy,
    OperationalNegotiationRequest,
)

import uuid

_PRESSURE_TO_STRATEGY: list[tuple[float, NegotiationStrategy]] = [
    (0.90, "temporary_degradation"),
    (0.80, "elastic_reallocation"),
    (0.70, "reasoning_compression"),
    (0.60, "optimization_deferral"),
    (0.50, "governance_batching"),
    (0.00, "no_action"),
]

_STRATEGY_DESCRIPTIONS: dict[NegotiationStrategy, str] = {
    "temporary_degradation":  "Temporarily degrade lowest-priority workflow quality to free capacity.",
    "reasoning_compression":  "Switch lower-priority workflows to shallow reasoning mode.",
    "optimization_deferral":  "Defer non-critical optimization passes to later execution windows.",
    "staged_execution":       "Break execution into lightweight progressive passes.",
    "elastic_reallocation":   "Shift excess capacity from low-priority to high-priority workflows.",
    "governance_batching":    "Batch governance reviews to reduce approval bandwidth consumption.",
    "no_action":              "Resource pressure within acceptable limits — no action needed.",
}


class NegotiationStrategyEngine:
    """Selects and describes negotiation strategies based on pressure."""

    def select(
        self,
        resource_pressure: float,
        pending_approvals: int = 0,
        has_critical_workflow: bool = False,
    ) -> NegotiationStrategy:
        """Pick the best strategy for current pressure level."""
        # Governance batching prioritized when approval backlog is high
        if pending_approvals >= 4 and resource_pressure < 0.80:
            return "governance_batching"

        for threshold, strategy in _PRESSURE_TO_STRATEGY:
            if resource_pressure >= threshold:
                # Prefer elastic_reallocation over degradation when critical wf present
                if strategy == "temporary_degradation" and has_critical_workflow:
                    return "elastic_reallocation"
                return strategy

        return "no_action"

    def build_proposal(
        self,
        strategy: NegotiationStrategy,
        requester: OperationalNegotiationRequest,
        donor_workflows: list[str],
        resource_pressure: float,
    ) -> NegotiationProposal:
        """Produce a NegotiationProposal for the selected strategy."""
        adjustments = self._adjustments(strategy, requester, donor_workflows)
        impact      = self._impact_description(strategy, requester)
        risk        = "none" if resource_pressure < 0.75 else ("low" if resource_pressure < 0.88 else "medium")
        confidence  = max(0.55, round(1.0 - resource_pressure * 0.5, 2))

        return NegotiationProposal(
            proposal_id=str(uuid.uuid4())[:8],
            participating_workflows=[requester.workflow_id] + donor_workflows,
            proposed_adjustments=adjustments,
            expected_operational_impact=impact,
            governance_risk=risk,  # type: ignore[arg-type]
            confidence_score=confidence,
            strategy_used=strategy,
        )

    def describe(self, strategy: NegotiationStrategy) -> str:
        return _STRATEGY_DESCRIPTIONS.get(strategy, "Unknown strategy.")

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _adjustments(
        strategy: NegotiationStrategy,
        requester: OperationalNegotiationRequest,
        donors: list[str],
    ) -> list[str]:
        donor_str = ", ".join(donors) if donors else "lower-priority workflows"
        req_id    = requester.workflow_id

        mapping: dict[NegotiationStrategy, list[str]] = {
            "temporary_degradation": [
                f"{donor_str} switched to compressed analysis mode.",
                f"Freed capacity redirected to '{req_id}'.",
            ],
            "reasoning_compression": [
                f"{donor_str} switched to shallow reasoning mode.",
                f"Deep reasoning reserved for '{req_id}'.",
            ],
            "optimization_deferral": [
                f"{donor_str} deferred non-critical optimization cycles.",
                "Optimization resumes after pressure normalizes.",
            ],
            "staged_execution": [
                f"'{req_id}' execution broken into lightweight progressive passes.",
                "Each pass runs under reduced resource envelope.",
            ],
            "elastic_reallocation": [
                f"{donor_str} reduced {requester.requested_resource} allocation by 20–30%.",
                f"'{req_id}' receives temporary capacity boost.",
            ],
            "governance_batching": [
                "Non-critical governance reviews batched into scheduled windows.",
                "Approval bandwidth freed for priority workflows.",
            ],
            "no_action": ["No adjustments required — system within operational bounds."],
        }
        return mapping.get(strategy, ["No adjustments specified."])

    @staticmethod
    def _impact_description(
        strategy: NegotiationStrategy,
        requester: OperationalNegotiationRequest,
    ) -> str:
        mapping: dict[NegotiationStrategy, str] = {
            "temporary_degradation": (
                "Lower-priority workflow quality slightly reduced. "
                "Critical workflow throughput preserved. Reversible on pressure drop."
            ),
            "reasoning_compression": (
                "Shallow reasoning used for background tasks. "
                "Analysis quality reduced temporarily. Full reasoning resumes automatically."
            ),
            "optimization_deferral": (
                "Non-critical optimizations delayed. "
                "Immediate execution quality maintained. Optimization resumes later."
            ),
            "staged_execution": (
                "Execution is slower but resource-efficient. "
                "Quality preserved across progressive passes."
            ),
            "elastic_reallocation": (
                "Lowest-priority workflows contribute excess capacity. "
                "Overall throughput improves for critical workflows."
            ),
            "governance_batching": (
                "Fewer governance interruptions. "
                "Review latency slightly increased for lower-priority changes."
            ),
            "no_action": "System stable — no operational impact.",
        }
        return mapping.get(strategy, "Impact unknown.")
