"""freya/hitl/semantic/governance.py

SemanticGovernanceValidator — evaluates a SemanticGuidanceIntent against
governance safety rules and returns a GovernanceIntentDecision.

Policy rules (evaluated in priority order):
  1. governance_bypass_attempt → always blocked, critical risk
  2. execution_policy_change   → allowed with medium risk, escalate if low confidence
  3. constraint_modification   → allowed, low risk
  4. approval / rejection      → always allowed, no risk
  5. *                         → allowed, appropriate risk for category
"""
from __future__ import annotations

from freya.hitl.semantic.models import (
    GovernanceIntentDecision,
    GovernanceRisk,
    SemanticGuidanceIntent,
)

# Risk level per category (default — may be overridden by confidence)
_CATEGORY_RISK: dict[str, GovernanceRisk] = {
    "approval":                 "none",
    "rejection":                "none",
    "governance_bypass_attempt": "critical",
    "execution_policy_change":  "medium",
    "constraint_modification":  "low",
    "priority_change":          "low",
    "optimization_request":     "none",
    "operational_guidance":     "none",
    "ambiguous_instruction":    "low",
}

_BLOCK_CATEGORIES = {"governance_bypass_attempt"}

# Messages
_BYPASS_REASON = (
    "Governance bypass is not permitted. "
    "Requests to skip, disable, or ignore approval and review controls are "
    "automatically rejected. Please use the standard approval workflow."
)
_LOW_CONFIDENCE_REASON = (
    "The intent could not be interpreted with sufficient confidence. "
    "Escalated to governance review to prevent unsafe workflow mutation."
)


class SemanticGovernanceValidator:
    """Validate a SemanticGuidanceIntent and return a GovernanceIntentDecision."""

    # Below this confidence, execution_policy_change escalates to governance review
    LOW_CONFIDENCE_THRESHOLD = 0.60

    def validate(self, intent: SemanticGuidanceIntent) -> GovernanceIntentDecision:
        """Evaluate the intent and return the decision."""
        cat = intent.semantic_category

        # Rule 1: governance bypass — always blocked
        if cat == "governance_bypass_attempt":
            return GovernanceIntentDecision(
                allowed=False,
                classification=cat,
                reason=_BYPASS_REASON,
                escalation_required=True,
                risk_level="critical",
            )

        # Rule 2: execution policy change — escalate if low confidence
        if cat == "execution_policy_change":
            if intent.confidence_score < self.LOW_CONFIDENCE_THRESHOLD:
                return GovernanceIntentDecision(
                    allowed=False,
                    classification=cat,
                    reason=_LOW_CONFIDENCE_REASON,
                    escalation_required=True,
                    risk_level="medium",
                )
            return GovernanceIntentDecision(
                allowed=True,
                classification=cat,
                reason="Execution policy change allowed; no governance controls affected.",
                escalation_required=False,
                risk_level="medium",
            )

        # Rule 3: ambiguous instruction — require clarification before allowing
        if cat == "ambiguous_instruction":
            return GovernanceIntentDecision(
                allowed=False,
                classification=cat,
                reason="Instruction is ambiguous. Clarification requested before any action.",
                escalation_required=False,
                risk_level="low",
            )

        # Default: allowed
        risk = _CATEGORY_RISK.get(cat, "none")
        return GovernanceIntentDecision(
            allowed=True,
            classification=cat,
            reason=f"Intent classified as '{cat}'. No governance controls affected.",
            escalation_required=False,
            risk_level=risk,  # type: ignore[arg-type]
        )

    def is_safe_to_apply(self, intent: SemanticGuidanceIntent) -> bool:
        """Quick check — True only if the intent is unambiguously safe."""
        decision = self.validate(intent)
        return decision.allowed and not decision.escalation_required
