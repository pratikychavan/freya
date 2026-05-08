from __future__ import annotations

from freya.governance.base import InterventionPolicy
from freya.governance.models import GovernanceDecision, InterventionDecision

_DANGEROUS_TOOLS = frozenset({
    "delete_data",
    "send_money",
    "external_mutation",
})


class CognitiveModeApprovalPolicy(InterventionPolicy):
    """Require human approval for any COGNITIVE mode workflow."""

    def evaluate(
        self,
        planning_context: object,
        proposed_dag: object,
    ) -> GovernanceDecision:
        from freya.planner.mode import PlanningMode  # local import to avoid circularity

        mode = getattr(planning_context, "planning_mode", None)
        if mode == PlanningMode.COGNITIVE:
            return GovernanceDecision(
                decision=InterventionDecision.REQUIRE_APPROVAL,
                reason="Cognitive mode workflows require approval.",
                risk_level="medium",
                triggered_policies=["CognitiveModeApprovalPolicy"],
            )
        return GovernanceDecision(
            decision=InterventionDecision.APPROVE,
            reason="Deterministic mode — no approval required.",
        )


class DangerousToolPolicy(InterventionPolicy):
    """Require approval when the proposed DAG references a dangerous tool."""

    def __init__(self, dangerous_tools: frozenset[str] | None = None) -> None:
        self._dangerous = dangerous_tools if dangerous_tools is not None else _DANGEROUS_TOOLS

    def evaluate(
        self,
        planning_context: object,
        proposed_dag: object,
    ) -> GovernanceDecision:
        tasks = getattr(proposed_dag, "tasks", [])
        found: list[str] = []
        for task in tasks:
            inp = getattr(task, "input", {}) or {}
            tool_name: str | None = None
            if isinstance(inp, dict):
                tool_name = inp.get("tool_name")
            else:
                tool_name = getattr(inp, "tool_name", None)
            if tool_name and tool_name in self._dangerous:
                found.append(tool_name)

        if found:
            return GovernanceDecision(
                decision=InterventionDecision.REQUIRE_APPROVAL,
                reason=f"DAG references dangerous tool(s): {', '.join(found)}.",
                risk_level="high",
                triggered_policies=["DangerousToolPolicy"],
            )
        return GovernanceDecision(
            decision=InterventionDecision.APPROVE,
            reason="No dangerous tools detected.",
        )


class ExcessiveRecoveryPolicy(InterventionPolicy):
    """Require approval when recovery attempts across the session exceed a threshold."""

    def __init__(self, threshold: int = 1) -> None:
        self._threshold = threshold

    def evaluate(
        self,
        planning_context: object,
        proposed_dag: object,
    ) -> GovernanceDecision:
        observations = getattr(planning_context, "recent_observations", [])
        recovery_count = sum(
            1 for o in observations if getattr(o, "recovery_attempted", False)
        )
        if recovery_count > self._threshold:
            return GovernanceDecision(
                decision=InterventionDecision.REQUIRE_APPROVAL,
                reason=(
                    f"Excessive runtime recovery attempts detected "
                    f"({recovery_count} > threshold {self._threshold})."
                ),
                risk_level="high",
                triggered_policies=["ExcessiveRecoveryPolicy"],
            )
        return GovernanceDecision(
            decision=InterventionDecision.APPROVE,
            reason="Recovery attempts within acceptable limits.",
        )
