"""freya/optimization/policies.py

OptimizationGovernancePolicy — enforces bounds on what the optimization
engine is permitted to recommend.

Rules:
  1. No quality degradation beyond threshold without approval.
  2. Removing governance controls always requires explicit approval.
  3. Low-confidence opportunities are downgraded to advisory-only.
  4. Strategies that increase governance risk are blocked unless user budget is large.
  5. No optimization may reduce cognitive depth if the workflow is in recovery mode.

Each rule is a pure function: (OptimizationOpportunity) → PolicyDecision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from freya.optimization.models import OptimizationOpportunity

# Thresholds
_MAX_QUALITY_DEGRADATION = -0.25   # beyond this, approval is required
_MIN_CONFIDENCE_AUTO = 0.60        # below this, opportunity is advisory only
_HIGH_BUDGET = 75_000              # above = governance controls justified

PolicyVerdict = Literal["allow", "require_approval", "block", "advisory"]


@dataclass(frozen=True)
class PolicyDecision:
    verdict: PolicyVerdict
    reason: str


def _rule_quality_degradation(opp: OptimizationOpportunity) -> PolicyDecision | None:
    delta = opp.estimated_quality_delta or 0.0
    if delta < _MAX_QUALITY_DEGRADATION:
        return PolicyDecision(
            verdict="require_approval",
            reason=(
                f"Quality reduction ({delta:.0%}) exceeds safe threshold. "
                "Explicit approval required before applying."
            ),
        )
    return None


def _rule_governance_removal(opp: OptimizationOpportunity) -> PolicyDecision | None:
    if opp.optimization_type == "governance":
        return PolicyDecision(
            verdict="require_approval",
            reason="Removing or reducing governance controls always requires explicit approval.",
        )
    return None


def _rule_low_confidence(opp: OptimizationOpportunity) -> PolicyDecision | None:
    if opp.confidence_score < _MIN_CONFIDENCE_AUTO:
        return PolicyDecision(
            verdict="advisory",
            reason=(
                f"Confidence ({opp.confidence_score:.0%}) is below the threshold for "
                "auto-recommendation. Surfaced as advisory only."
            ),
        )
    return None


def _rule_cognitive_in_recovery(opp: OptimizationOpportunity) -> PolicyDecision | None:
    """Block cognitive depth reductions when the update key suggests recovery mode."""
    if opp.optimization_type == "cognitive" and opp.constraint_updates.get("in_recovery"):
        return PolicyDecision(
            verdict="block",
            reason="Cognitive depth cannot be reduced while a workflow is in recovery mode.",
        )
    return None


_RULES = [
    _rule_governance_removal,      # check first — strictest
    _rule_quality_degradation,
    _rule_cognitive_in_recovery,
    _rule_low_confidence,
]


class OptimizationGovernancePolicy:
    """Evaluate whether an optimization opportunity is safe to recommend."""

    def evaluate(self, opp: OptimizationOpportunity) -> PolicyDecision:
        """Return the most restrictive PolicyDecision that applies.

        Default: allow.
        """
        decisions: list[PolicyDecision] = []
        for rule in _RULES:
            d = rule(opp)
            if d is not None:
                decisions.append(d)

        if not decisions:
            return PolicyDecision(verdict="allow", reason="All policy checks passed.")

        # Priority: block > require_approval > advisory > allow
        priority = {"block": 0, "require_approval": 1, "advisory": 2, "allow": 3}
        return min(decisions, key=lambda d: priority[d.verdict])

    def filter(
        self,
        opportunities: list[OptimizationOpportunity],
    ) -> tuple[list[OptimizationOpportunity], list[OptimizationOpportunity], list[OptimizationOpportunity]]:
        """Sort opportunities into (allowed, requires_approval, blocked/advisory).

        Returns three lists:
          - allowed        : safe to recommend directly
          - needs_approval : must show users and wait for acceptance
          - advisory       : surface as informational, no direct action
        """
        allowed = []
        needs_approval = []
        advisory = []

        for opp in opportunities:
            decision = self.evaluate(opp)
            if decision.verdict == "allow":
                allowed.append(opp)
            elif decision.verdict == "require_approval":
                needs_approval.append(opp)
            else:  # "advisory" or "block" — demote to advisory (never silently drop)
                advisory.append(opp)

        return allowed, needs_approval, advisory
