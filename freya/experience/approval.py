"""freya/experience/approval.py

Converts raw governance ApprovalRequest objects into human-readable
ApprovalExperience objects.

The builder extracts key signals (budget overrun, policy names, risk)
and renders them in business language — no runtime jargon exposed.
"""
from __future__ import annotations

import re

from freya.experience.models import ApprovalExperience


# ---------------------------------------------------------------------------
# Policy-name → human explanation mapping
# ---------------------------------------------------------------------------

POLICY_EXPLANATIONS: dict[str, str] = {
    "HotelOverBudgetPolicy": (
        "The recommended hotel exceeds your preferred budget."
    ),
    "HighCostApprovalPolicy": (
        "The total trip cost exceeds your configured approval threshold."
    ),
    "DangerousToolPolicy": (
        "A sensitive operation requires your explicit approval before proceeding."
    ),
}

# ---------------------------------------------------------------------------
# Budget overrun extractor
# Parses governance_reason strings like:
#   "… costs ₹18,000/night (₹36,000 for 2 nights), exceeding preferred budget of ₹20,000 …"
# ---------------------------------------------------------------------------

_AMOUNT_RE = re.compile(r"₹[\d,]+")


def _extract_amounts(text: str) -> list[str]:
    return _AMOUNT_RE.findall(text)


def _build_budget_impact(reason: str, risk_level: str | None) -> str:
    amounts = _extract_amounts(reason)
    if len(amounts) >= 2:
        actual, limit = amounts[0], amounts[1]
        return (
            f"  Selected option : {actual}\n"
            f"  Preferred limit : {limit}\n"
            f"  Risk level      : {(risk_level or 'medium').upper()}"
        )
    return f"  Details : {reason}\n  Risk level : {(risk_level or 'medium').upper()}"


class ApprovalExperienceBuilder:
    """Converts a governance ApprovalRequest into an ApprovalExperience.

    Accepts either an ApprovalRequest Pydantic object or a plain dict
    (e.g., from a serialized snapshot).
    """

    def build(self, request: object) -> ApprovalExperience:
        # Support both ApprovalRequest objects and dicts
        if isinstance(request, dict):
            governance_reason: str = request.get("governance_reason", "")
            risk_level: str | None = request.get("risk_level")
            triggered_policies: list[str] = request.get("triggered_policies", [])
            request_id: str = request.get("request_id", "")
        else:
            governance_reason = getattr(request, "governance_reason", "")
            risk_level = getattr(request, "risk_level", None)
            triggered_policies = getattr(request, "triggered_policies", [])
            request_id = getattr(request, "request_id", "")

        # ── Build title ──────────────────────────────────────────────────
        title = "Approval Required"

        # ── Build human message ──────────────────────────────────────────
        human_message = self._human_message(governance_reason, triggered_policies)

        # ── Build impact summary ─────────────────────────────────────────
        impact = _build_budget_impact(governance_reason, risk_level)

        return ApprovalExperience(
            title=title,
            message=human_message,
            impact_summary=impact,
            choices=["Approve", "Reject"],
            risk_level=risk_level,
            metadata={"request_id": request_id, "raw_reason": governance_reason},
        )

    def _human_message(self, reason: str, policies: list[str]) -> str:
        # Try to find a clean explanation from the policy registry
        for policy in policies:
            if policy in POLICY_EXPLANATIONS:
                return POLICY_EXPLANATIONS[policy]

        # Fallback: strip runtime jargon and return normalized reason
        clean = reason.replace("HighCostApprovalPolicy", "cost policy")
        clean = clean.replace("HotelOverBudgetPolicy", "budget policy")
        # Trim to first sentence for brevity
        first_sentence = clean.split(".")[0].strip()
        return first_sentence + "." if first_sentence else reason

    def render_terminal(self, experience: ApprovalExperience) -> str:
        """Render the approval experience as a clean terminal block."""
        lines = [
            "",
            "  ╔══════════════════════════════════════════════════════════════╗",
            f"  ║  ⚠  {experience.title:<57}║",
            "  ╠══════════════════════════════════════════════════════════════╣",
            "  ║" + " " * 62 + "║",
            f"  ║  {experience.message:<60}║",
            "  ║" + " " * 62 + "║",
            "  ║  Impact:                                                      ║",
        ]
        for line in experience.impact_summary.splitlines():
            lines.append(f"  ║  {line:<60}║")
        lines += [
            "  ║" + " " * 62 + "║",
            "  ╠══════════════════════════════════════════════════════════════╣",
        ]
        choices_str = "  ".join(f"[{c}]" for c in experience.choices)
        lines.append(f"  ║  Options: {choices_str:<52}║")
        lines.append("  ╚══════════════════════════════════════════════════════════════╝")
        lines.append("")
        return "\n".join(lines)
