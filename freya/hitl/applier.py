"""freya/hitl/applier.py

HumanGuidanceApplier — safely applies a parsed HumanGuidance to a
WorkflowSteeringState and optionally triggers optimization reassessment.

Design rules:
  - Every possible state mutation is recorded in GuidanceApplicationResult.
  - Governance state is preserved — no bypassing.
  - Prefer targeted mutations; never restart the whole workflow.
  - Returns a structured result with human-readable narrative.
"""
from __future__ import annotations

from typing import Any

from freya.hitl.models import GuidanceApplicationResult, HumanGuidance
from freya.optimization import OptimizationAdvisor
from freya.steering import SteeringCoordinator
from freya.steering.models import WorkflowSteeringState

_PRIORITY_MAP = {
    "cost":        "cost",
    "speed":       "speed",
    "quality":     "quality",
    "convenience": "balanced",
    "balanced":    "balanced",
}


class HumanGuidanceApplier:
    """Translate a HumanGuidance into concrete WorkflowSteeringState mutations."""

    def __init__(self) -> None:
        self._coordinator = SteeringCoordinator()
        self._advisor = OptimizationAdvisor()

    def apply(
        self,
        guidance: HumanGuidance,
        state: WorkflowSteeringState,
    ) -> GuidanceApplicationResult:
        """Apply guidance to state. Returns a detailed result record."""
        applied: list[str] = []
        updates: list[str] = []
        gov_actions: list[str] = []

        gtype = guidance.guidance_type

        # ── Approve / Reject ────────────────────────────────────────
        if gtype == "approve":
            return GuidanceApplicationResult(
                success=True,
                applied_changes=["Approval recorded"],
                workflow_updates=["Workflow authorised to continue"],
                governance_actions=["Approval checkpoint cleared"],
                narrative_summary="User approved. Workflow continuing.",
            )
        if gtype == "reject":
            return GuidanceApplicationResult(
                success=True,
                applied_changes=["Rejection recorded"],
                workflow_updates=["Workflow stopped at approval checkpoint"],
                governance_actions=["Rejection logged"],
                narrative_summary="User rejected. Workflow halted.",
            )

        # ── Cost adjustment ─────────────────────────────────────────
        if gtype == "cost_adjustment":
            budget_target = guidance.extracted_constraints.get("budget_target")
            if budget_target:
                self._coordinator.modify_constraint(state, "budget_inr", budget_target)
                applied.append(f"Budget target set to ₹{budget_target:,}")
                updates.append("Budget constraint updated")
            # Also steer toward cost
            decision = self._coordinator.steer(state, "cost")
            applied.append(decision.narrative)
            updates.append("Priority set to cost")

        # ── Priority change ─────────────────────────────────────────
        elif gtype == "priority_change":
            priority = guidance.extracted_preferences.get("priority", "balanced")
            mapped = _PRIORITY_MAP.get(priority, "balanced")
            decision = self._coordinator.steer(state, mapped)
            applied.append(decision.narrative)
            updates.append(f"Execution priority changed to {mapped}")

        # ── Preference update ───────────────────────────────────────
        elif gtype == "preference_update":
            avoid = guidance.extracted_preferences.get("avoid")
            prefer = guidance.extracted_preferences.get("prefer")
            metro = guidance.extracted_preferences.get("metro_access")
            venue = guidance.extracted_preferences.get("venue_proximity")

            if avoid:
                self._coordinator._steerer._set_preference(state, f"avoid_{avoid.replace(' ', '_')}", "true")
                applied.append(f"Avoid preference recorded: {avoid}")
                updates.append(f"Excluded: {avoid}")
            if prefer:
                self._coordinator._steerer._set_preference(state, "preferred_location", prefer)
                applied.append(f"Preference recorded: {prefer}")
                updates.append(f"Preferred: {prefer}")
            if metro:
                self._coordinator._steerer._set_preference(state, "metro_access", "preferred")
                applied.append("Metro proximity preference set")
                updates.append("Hotel search will prioritise metro access")
            if venue:
                self._coordinator._steerer._set_preference(state, "venue_proximity", "preferred")
                applied.append("Venue proximity preference set")
                updates.append("Hotel search will prioritise venue proximity")

        # ── Execution depth change ──────────────────────────────────
        elif gtype == "execution_depth_change":
            state.set_strategy("deterministic")
            applied.append("Analysis depth reduced")
            updates.append("Strategy set to deterministic (fast mode)")

        # ── Optimization request ────────────────────────────────────
        elif gtype == "optimization_request":
            proposal = self._advisor.propose(state)
            if proposal:
                for opp in proposal.opportunities:
                    try:
                        changes = self._advisor.apply_opportunity(state, opp)
                        applied.append(f"Applied: {opp.title}")
                        for k, v in changes.items():
                            updates.append(f"{k.replace('_', ' ').title()}: {v}")
                    except ValueError as e:
                        gov_actions.append(f"Blocked: {opp.title} — {e}")
            else:
                updates.append("No optimization opportunities identified at this time")

        # ── Recovery policy change ──────────────────────────────────
        elif gtype == "recovery_policy_change":
            retries = guidance.extracted_constraints.get("max_retries", 2)
            self._coordinator.modify_constraint(state, "max_retries", retries)
            applied.append(f"Max retries set to {retries}")
            updates.append("Recovery policy updated")

        # ── Governance override (blocked) ───────────────────────────
        elif gtype == "governance_override_request":
            gov_actions.append("Governance override request logged — requires explicit escalation")
            return GuidanceApplicationResult(
                success=False,
                applied_changes=[],
                workflow_updates=[],
                governance_actions=gov_actions,
                narrative_summary="Governance override requires escalation and is not auto-applied.",
            )

        # ── Unknown ─────────────────────────────────────────────────
        else:
            return GuidanceApplicationResult(
                success=False,
                applied_changes=[],
                workflow_updates=["Guidance type not recognised — no changes applied"],
                governance_actions=[],
                narrative_summary=f"Guidance could not be interpreted: \"{guidance.raw_input[:60]}\"",
            )

        # ── Post-apply: governance impact check ─────────────────────
        new_gov = self._coordinator.governance_impact(state)
        if new_gov:
            for req in new_gov:
                gov_actions.append(f"Governance: {req.replace('_', ' ')}")

        narrative = _build_narrative(guidance, applied, updates)
        return GuidanceApplicationResult(
            success=True,
            applied_changes=applied,
            workflow_updates=updates,
            governance_actions=gov_actions,
            narrative_summary=narrative,
        )


def _build_narrative(
    guidance: HumanGuidance,
    applied: list[str],
    updates: list[str],
) -> str:
    if not applied:
        return "No changes applied."
    primary = applied[0]
    extras = len(applied) - 1
    tail = f" (+{extras} more change{'s' if extras > 1 else ''})" if extras else ""
    return f"{primary}{tail}. Workflow reassessing..."
