"""freya/hitl/governance.py

HumanGuidanceGovernance — validates human guidance before it is applied
to ensure it stays within safe, governed bounds.

Rules (evaluated in order, most restrictive first):
  1. Governance override requests are always escalated.
  2. Preference updates that disable safety checks are blocked.
  3. Budget increases beyond threshold require approval.
  4. Unknown guidance is flagged as low-risk advisory.
  5. Everything else is allowed.
"""
from __future__ import annotations

from freya.hitl.models import GuidanceGovernanceDecision, HumanGuidance

# Thresholds
_BUDGET_ESCALATION_THRESHOLD = 75_000   # INR — above this, budget changes need approval
_BUDGET_AUTO_INCREASE_MAX = 20_000      # maximum auto-approved budget increase


class HumanGuidanceGovernance:
    """Validate human guidance before it is applied to the workflow."""

    def evaluate(self, guidance: HumanGuidance) -> GuidanceGovernanceDecision:
        """Return a governance decision for the given guidance."""
        gtype = guidance.guidance_type

        # ── Governance override — always escalate ────────────────────
        if gtype == "governance_override_request":
            return GuidanceGovernanceDecision(
                allowed=False,
                reason=(
                    "Governance override requests cannot be auto-applied. "
                    "Escalate to a workflow administrator."
                ),
                requires_approval=True,
                risk_level="high",
            )

        # ── Budget changes above threshold ───────────────────────────
        budget_target = guidance.extracted_constraints.get("budget_target")
        if budget_target and float(budget_target) > _BUDGET_ESCALATION_THRESHOLD:
            return GuidanceGovernanceDecision(
                allowed=False,
                reason=(
                    f"Budget target ₹{int(budget_target):,} exceeds the auto-approval "
                    f"limit of ₹{_BUDGET_ESCALATION_THRESHOLD:,}. Manager approval required."
                ),
                requires_approval=True,
                risk_level="medium",
            )

        # ── Cost-reduction guidance — always safe ────────────────────
        if gtype == "cost_adjustment":
            return GuidanceGovernanceDecision(
                allowed=True,
                reason="Cost reduction guidance is within safe bounds.",
                requires_approval=False,
                risk_level="none",
            )

        # ── Priority change — safe ───────────────────────────────────
        if gtype == "priority_change":
            return GuidanceGovernanceDecision(
                allowed=True,
                reason="Priority adjustment is within governed bounds.",
                requires_approval=False,
                risk_level="none",
            )

        # ── Preference update — safe unless disabling safety ─────────
        if gtype == "preference_update":
            avoid = guidance.extracted_preferences.get("avoid", "")
            if any(w in avoid.lower() for w in ("governance", "approval", "review")):
                return GuidanceGovernanceDecision(
                    allowed=False,
                    reason="Cannot disable governance or approval checks via preference update.",
                    requires_approval=False,
                    risk_level="high",
                )
            return GuidanceGovernanceDecision(
                allowed=True,
                reason="Preference update is within safe bounds.",
                requires_approval=False,
                risk_level="none",
            )

        # ── Execution depth change — low risk ────────────────────────
        if gtype == "execution_depth_change":
            return GuidanceGovernanceDecision(
                allowed=True,
                reason="Execution depth change does not affect governance or safety.",
                requires_approval=False,
                risk_level="low",
            )

        # ── Optimization request — safe ──────────────────────────────
        if gtype == "optimization_request":
            return GuidanceGovernanceDecision(
                allowed=True,
                reason="Optimization request deferred to policy-gated engine.",
                requires_approval=False,
                risk_level="none",
            )

        # ── Recovery policy change — low risk ────────────────────────
        if gtype == "recovery_policy_change":
            return GuidanceGovernanceDecision(
                allowed=True,
                reason="Recovery policy changes are within safe operational bounds.",
                requires_approval=False,
                risk_level="low",
            )

        # ── Approve / Reject — always allowed ───────────────────────
        if gtype in ("approve", "reject"):
            return GuidanceGovernanceDecision(
                allowed=True,
                reason="Standard approval action.",
                requires_approval=False,
                risk_level="none",
            )

        # ── Unknown — advisory, allow with warning ───────────────────
        return GuidanceGovernanceDecision(
            allowed=True,
            reason="Guidance type unknown — treated as advisory. Minimal changes applied.",
            requires_approval=False,
            risk_level="low",
        )
