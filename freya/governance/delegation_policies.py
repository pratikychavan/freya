from __future__ import annotations

from freya.governance.base import InterventionPolicy
from freya.governance.models import GovernanceDecision, InterventionDecision


class ExcessiveDelegationDepthPolicy(InterventionPolicy):
    """Reject delegation when the workflow tree depth would exceed a limit.

    Computes depth by walking up the WorkflowCoordinator ancestry chain.
    A ``max_depth`` of 1 allows only root → one child level.
    """

    def __init__(self, max_depth: int = 3) -> None:
        self._max_depth = max_depth

    def evaluate(
        self,
        planning_context: object,
        proposed_dag: object,
    ) -> GovernanceDecision:
        coordinator = getattr(planning_context, "_coordinator_ref", None)
        session_id = getattr(planning_context, "session_id", None)

        if coordinator is None or session_id is None:
            return GovernanceDecision(
                decision=InterventionDecision.APPROVE,
                reason="No coordinator context — depth check skipped.",
            )

        depth = _compute_depth(coordinator, session_id)
        if depth >= self._max_depth:
            return GovernanceDecision(
                decision=InterventionDecision.REJECT,
                reason=(
                    f"Delegation hierarchy depth {depth} would exceed "
                    f"maximum allowed depth {self._max_depth}."
                ),
                risk_level="high",
                triggered_policies=["ExcessiveDelegationDepthPolicy"],
            )
        return GovernanceDecision(
            decision=InterventionDecision.APPROVE,
            reason=f"Delegation depth {depth} is within limit {self._max_depth}.",
        )


class MissingCapabilityPolicy(InterventionPolicy):
    """Reject delegation when a required capability is unavailable.

    Inspects ``planning_context._pending_contract`` (set by the runner just
    before governance evaluation of a proposed delegation).
    """

    def evaluate(
        self,
        planning_context: object,
        proposed_dag: object,
    ) -> GovernanceDecision:
        contract = getattr(planning_context, "_pending_contract", None)
        if contract is None:
            return GovernanceDecision(
                decision=InterventionDecision.APPROVE,
                reason="No pending delegation contract — capability check skipped.",
            )

        tool_registry = getattr(planning_context, "_tool_registry_ref", None)
        prompt_registry = getattr(planning_context, "_prompt_registry_ref", None)

        available: set[str] = set()
        if tool_registry is not None:
            available.update(tool_registry.list_tools())
        if prompt_registry is not None:
            available.update(prompt_registry.list_capabilities())

        required: list[str] = getattr(contract, "required_capabilities", [])
        missing = [cap for cap in required if cap not in available]

        if missing:
            return GovernanceDecision(
                decision=InterventionDecision.REJECT,
                reason=f"Delegation requires unavailable capabilities: {', '.join(missing)}.",
                risk_level="high",
                triggered_policies=["MissingCapabilityPolicy"],
            )
        return GovernanceDecision(
            decision=InterventionDecision.APPROVE,
            reason="All required capabilities are available.",
        )


class DelegationBudgetPolicy(InterventionPolicy):
    """Reject delegation when the number of child workflows would exceed a budget.

    Counts current children of the session in the coordinator.
    """

    def __init__(self, max_children: int = 5) -> None:
        self._max_children = max_children

    def evaluate(
        self,
        planning_context: object,
        proposed_dag: object,
    ) -> GovernanceDecision:
        coordinator = getattr(planning_context, "_coordinator_ref", None)
        session_id = getattr(planning_context, "session_id", None)

        if coordinator is None or session_id is None:
            return GovernanceDecision(
                decision=InterventionDecision.APPROVE,
                reason="No coordinator context — budget check skipped.",
            )

        current_children = len(coordinator.get_children(session_id))
        if current_children >= self._max_children:
            return GovernanceDecision(
                decision=InterventionDecision.REJECT,
                reason=(
                    f"Delegation budget exceeded: {current_children} child workflow(s) "
                    f"already spawned (max {self._max_children})."
                ),
                risk_level="high",
                triggered_policies=["DelegationBudgetPolicy"],
            )
        return GovernanceDecision(
            decision=InterventionDecision.APPROVE,
            reason=f"Delegation budget {current_children}/{self._max_children} within limits.",
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_depth(coordinator: object, session_id: str) -> int:
    """Walk up the coordinator ancestry chain and return the depth of session_id."""
    depth = 0
    current = session_id
    seen: set[str] = set()
    while True:
        parent = coordinator.get_parent(current)  # type: ignore[attr-defined]
        if parent is None:
            break
        if parent in seen:
            break  # cycle guard
        seen.add(parent)
        depth += 1
        current = parent
    return depth
