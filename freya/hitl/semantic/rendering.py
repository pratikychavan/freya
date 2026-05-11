"""freya/hitl/semantic/rendering.py

Human-centered terminal rendering for the Semantic Governance Cognition layer.

Design rules:
  - Auditable: always shows classification + confidence + governance verdict
  - Concise: no verbose AI chat language
  - Enterprise-grade: governance risk is prominent when present
  - Blocked inputs show a clear, actionable explanation
"""
from __future__ import annotations

from freya.hitl.semantic.models import (
    ClarificationRequest,
    GovernanceIntentDecision,
    SemanticGuidanceIntent,
)

# ── ANSI ─────────────────────────────────────────────────────────────
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_MAGENTA = "\033[95m"
_RED = "\033[91m"
_RESET = "\033[0m"

_DIVIDER = f"{_CYAN}{'─' * 66}{_RESET}"

_RISK_COLOURS = {
    "none":     _GREEN,
    "low":      _CYAN,
    "medium":   _YELLOW,
    "high":     _MAGENTA,
    "critical": _RED,
}
_CATEGORY_LABELS: dict[str, str] = {
    "approval":                 "Approval",
    "rejection":                "Rejection",
    "governance_bypass_attempt": "⛔ Governance Bypass Attempt",
    "execution_policy_change":  "Execution Policy Change",
    "constraint_modification":  "Constraint Modification",
    "priority_change":          "Priority Change",
    "optimization_request":     "Optimization Request",
    "operational_guidance":     "Operational Guidance",
    "ambiguous_instruction":    "Ambiguous Instruction",
}


def render_semantic_classification(intent: SemanticGuidanceIntent) -> str:
    """Render a SemanticGuidanceIntent classification panel."""
    risk_colour = _RISK_COLOURS.get(intent.governance_risk, "")
    cat_label = _CATEGORY_LABELS.get(intent.semantic_category, intent.semantic_category)

    conf_pct = int(intent.confidence_score * 100)
    if intent.confidence_score >= 0.80:
        conf_str = f"{_GREEN}High ({conf_pct}%){_RESET}"
    elif intent.confidence_score >= 0.60:
        conf_str = f"{_CYAN}Medium ({conf_pct}%){_RESET}"
    elif intent.confidence_score >= 0.40:
        conf_str = f"{_YELLOW}Low ({conf_pct}%){_RESET}"
    else:
        conf_str = f"{_RED}Very Low ({conf_pct}%){_RESET}"

    lines = [
        _DIVIDER,
        f"{_BOLD}  Guidance Classification{_RESET}",
        "",
        f"  Input:          {_DIM}\"{intent.raw_input[:72]}\"{_RESET}",
        f"  Detected Intent: {intent.interpreted_intent}",
        f"  Category:       {_BOLD}{cat_label}{_RESET}",
        f"  Confidence:     {conf_str}",
        f"  Governance Risk: {risk_colour}{intent.governance_risk.title()}{_RESET}",
        f"  Method:         {intent.parse_method}",
    ]

    if intent.extracted_constraints:
        lines.append("")
        lines.append(f"  {_BOLD}Extracted Constraints{_RESET}")
        for k, v in intent.extracted_constraints.items():
            label = k.replace("_", " ").title()
            if "budget" in k and isinstance(v, (int, float)):
                sign = "+" if v > 0 else ""
                v = f"{sign}₹{abs(int(v)):,}"
            lines.append(f"    • {label}: {v}")

    if intent.extracted_preferences:
        lines.append("")
        lines.append(f"  {_BOLD}Extracted Preferences{_RESET}")
        for k, v in intent.extracted_preferences.items():
            label = k.replace("_", " ").title()
            lines.append(f"    • {label}: {v}")

    if intent.requires_clarification:
        lines.append("")
        lines.append(f"  {_YELLOW}⚠  Clarification required before any action is taken.{_RESET}")
    if intent.requires_governance_review:
        lines.append("")
        lines.append(f"  {_RED}🔒 Governance review required.{_RESET}")

    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_governance_decision(decision: GovernanceIntentDecision) -> str:
    """Render a GovernanceIntentDecision panel."""
    risk_colour = _RISK_COLOURS.get(decision.risk_level, "")
    if decision.allowed:
        status = f"{_GREEN}✓  Allowed{_RESET}"
    else:
        status = f"{_RED}✗  Blocked{_RESET}"

    lines = [
        _DIVIDER,
        f"{_BOLD}  Governance Decision{_RESET}",
        "",
        f"  Status:     {status}",
        f"  Reason:     {decision.reason}",
        f"  Risk Level: {risk_colour}{decision.risk_level.title()}{_RESET}",
    ]
    if decision.escalation_required:
        lines.append(f"  {_YELLOW}⚑  Escalated to governance review.{_RESET}")
    lines.append(_DIVIDER)
    return "\n".join(lines)


def render_clarification_request(clarification: ClarificationRequest) -> str:
    """Render a ClarificationRequest panel."""
    lines = [
        _DIVIDER,
        f"{_YELLOW}❓  Clarification Needed{_RESET}",
        "",
        f"  {clarification.clarification_question}",
        "",
        f"  {_BOLD}Options{_RESET}",
    ]
    for i, opt in enumerate(clarification.suggested_options, 1):
        lines.append(f"    {i}. {opt}")
    lines.append("")
    lines.append(f"  {_DIM}Reply with your choice or type a custom instruction.{_RESET}")
    lines.append(_DIVIDER)
    return "\n".join(lines)
