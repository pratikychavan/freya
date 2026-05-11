"""freya/hitl/cli.py

Professional terminal interaction layer for Advanced HITL.

Provides structured, workflow-oriented prompts rather than raw input().
Supports: approve / reject / operational guidance / optimization view / state inspect.

The CLI is fully synchronous and works in any terminal.
It does NOT build chatbot loops — each call collects exactly one
bounded interaction and returns a result.
"""
from __future__ import annotations

import asyncio
import sys
from typing import Literal

from freya.hitl.applier import HumanGuidanceApplier
from freya.hitl.governance import HumanGuidanceGovernance
from freya.hitl.interpreter import HumanGuidanceInterpreter
from freya.hitl.models import GuidanceApplicationResult, GuidanceAuditTrail, HumanGuidance
from freya.hitl.rendering import (
    render_guidance_interpreted,
    render_guidance_prompt,
    render_guidance_result,
    render_guidance_review,
)
from freya.optimization import OptimizationAdvisor, render_optimization_proposal
from freya.steering.models import WorkflowSteeringState
from freya.steering.rendering import render_steering_state

# ── ANSI ─────────────────────────────────────────────────────────────
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_RESET = "\033[0m"

_WIDTH = 66

HITLOutcome = Literal["approved", "rejected", "guidance_applied", "escalated", "cancelled"]


class HumanGuidanceCLI:
    """Professional HITL terminal interaction.

    Usage::

        cli = HumanGuidanceCLI()
        outcome, result = cli.interact(
            state=state,
            context="Hotel Selection",
            reason="Selected hotel exceeds preferred budget by ₹8,000.",
            current_recommendation="Business hotel near client office — ₹12,000/night.",
            audit_trail=trail,
        )
    """

    def __init__(self, llm_adapter: object | None = None) -> None:
        self._interpreter = HumanGuidanceInterpreter(llm_adapter)
        self._applier = HumanGuidanceApplier()
        self._governance = HumanGuidanceGovernance()
        self._advisor = OptimizationAdvisor()

    def interact(
        self,
        state: WorkflowSteeringState,
        context: str,
        reason: str,
        current_recommendation: str | None = None,
        audit_trail: GuidanceAuditTrail | None = None,
    ) -> tuple[HITLOutcome, GuidanceApplicationResult | None]:
        """Run one full HITL interaction cycle.

        Returns (outcome, result_or_None).
        Handles all rendering and input; caller just acts on the outcome.
        """
        print(render_guidance_prompt(context, reason, current_recommendation))

        while True:
            choice = self._read_choice("Select option [1/2/3/4]: ", valid={"1", "2", "3", "4"})

            if choice == "1":
                return self._handle_approve(audit_trail)

            if choice == "2":
                return self._handle_reject(audit_trail)

            if choice == "3":
                outcome, result = self._handle_guidance(state, audit_trail)
                return outcome, result

            if choice == "4":
                self._show_optimization(state)
                # Loop back — show prompt again without header
                self._print_mini_menu()
                continue

    # ── Option handlers ───────────────────────────────────────────────

    def _handle_approve(
        self, audit_trail: GuidanceAuditTrail | None
    ) -> tuple[HITLOutcome, GuidanceApplicationResult]:
        result = GuidanceApplicationResult(
            success=True,
            applied_changes=["Approval recorded"],
            workflow_updates=["Workflow authorised to continue"],
            governance_actions=["Approval checkpoint cleared"],
            narrative_summary="User approved. Workflow continuing.",
        )
        print(f"\n  {_GREEN}✓ Approved — workflow continuing.{_RESET}\n")
        return "approved", result

    def _handle_reject(
        self, audit_trail: GuidanceAuditTrail | None
    ) -> tuple[HITLOutcome, GuidanceApplicationResult]:
        result = GuidanceApplicationResult(
            success=True,
            applied_changes=["Rejection recorded"],
            workflow_updates=["Workflow stopped at approval checkpoint"],
            governance_actions=["Rejection logged"],
            narrative_summary="User rejected. Workflow halted.",
        )
        print(f"\n  {_YELLOW}✗ Rejected — workflow halted.{_RESET}\n")
        return "rejected", result

    def _handle_guidance(
        self,
        state: WorkflowSteeringState,
        audit_trail: GuidanceAuditTrail | None,
    ) -> tuple[HITLOutcome, GuidanceApplicationResult]:
        print(f"\n  {_BOLD}Enter operational guidance:{_RESET}")
        print(f"  {_DIM}Examples: \"find cheaper hotel\"  |  \"prioritise metro access\"  |  \"skip deep comparison\"{_RESET}")
        print(f"  {_DIM}Type your instruction and press Enter.{_RESET}\n")

        raw = input("  > ").strip()
        if not raw:
            print(f"  {_YELLOW}No input received — returning to menu.{_RESET}")
            return "cancelled", None

        print(f"\n  {_DIM}Processing guidance...{_RESET}")

        # Interpret — run async in sync context
        guidance = asyncio.get_event_loop().run_until_complete(
            self._interpreter.interpret(raw)
        )
        print(render_guidance_interpreted(guidance))

        # Governance check
        gov_decision = self._governance.evaluate(guidance)
        if not gov_decision.allowed:
            print(render_guidance_review(guidance, gov_decision))
            if audit_trail:
                _dummy_result = GuidanceApplicationResult(
                    success=False,
                    narrative_summary=f"Blocked: {gov_decision.reason}",
                )
                audit_trail.add(guidance, _dummy_result, "blocked")
            return "escalated", None

        # Apply
        result = self._applier.apply(guidance, state)
        print(render_guidance_result(result))

        if audit_trail:
            audit_trail.add(guidance, result, "allowed")

        # Re-run optimization assessment after state change
        proposal = self._advisor.reassess(state)
        if proposal:
            print(f"\n  {_CYAN}New optimization opportunities detected after guidance:{_RESET}")
            print(render_optimization_proposal(proposal))

        return "guidance_applied", result

    def _show_optimization(self, state: WorkflowSteeringState) -> None:
        proposal = self._advisor.propose(state)
        if proposal:
            print(render_optimization_proposal(proposal))
        else:
            print(f"\n  {_DIM}No optimization opportunities currently detected.{_RESET}\n")
        print(render_steering_state(state))

    # ── UI helpers ────────────────────────────────────────────────────

    def _read_choice(self, prompt: str, valid: set[str]) -> str:
        while True:
            raw = input(f"  {prompt}").strip()
            if raw in valid:
                return raw
            print(f"  {_YELLOW}Please enter one of: {', '.join(sorted(valid))}{_RESET}")

    def _print_mini_menu(self) -> None:
        print(f"\n  {_DIM}─ Options ──────────────────────{_RESET}")
        print(f"  [1] Approve  [2] Reject  [3] Provide Guidance  [4] View Optimization")
        print()


# ---------------------------------------------------------------------------
# Convenience: non-interactive simulation (for testing / demos)
# ---------------------------------------------------------------------------

class SimulatedGuidanceCLI:
    """A non-interactive version that accepts a pre-scripted choice and optional guidance.

    Used in demos and tests to avoid blocking on stdin.
    """

    def __init__(self, llm_adapter: object | None = None) -> None:
        self._interpreter = HumanGuidanceInterpreter(llm_adapter)
        self._applier = HumanGuidanceApplier()
        self._governance = HumanGuidanceGovernance()
        self._advisor = OptimizationAdvisor()

    async def simulate(
        self,
        state: WorkflowSteeringState,
        context: str,
        reason: str,
        current_recommendation: str | None,
        choice: Literal["approve", "reject", "guidance"],
        guidance_text: str = "",
        audit_trail: GuidanceAuditTrail | None = None,
    ) -> tuple[HITLOutcome, GuidanceApplicationResult | None]:
        """Run a simulated interaction without stdin."""
        print(render_guidance_prompt(context, reason, current_recommendation))

        if choice == "approve":
            result = GuidanceApplicationResult(
                success=True,
                applied_changes=["Approval recorded"],
                workflow_updates=["Workflow authorised to continue"],
                governance_actions=["Approval checkpoint cleared"],
                narrative_summary="User approved. Workflow continuing.",
            )
            print(f"  {_GREEN}✓ Approved — workflow continuing.{_RESET}\n")
            return "approved", result

        if choice == "reject":
            result = GuidanceApplicationResult(
                success=True,
                applied_changes=["Rejection recorded"],
                workflow_updates=["Workflow stopped"],
                governance_actions=["Rejection logged"],
                narrative_summary="User rejected. Workflow halted.",
            )
            print(f"  {_YELLOW}✗ Rejected — workflow halted.{_RESET}\n")
            return "rejected", result

        # Guidance
        if not guidance_text:
            return "cancelled", None

        print(f"  {_DIM}User provides guidance:{_RESET} {_YELLOW}\"{guidance_text}\"{_RESET}")
        print(f"  {_DIM}Processing...{_RESET}\n")

        guidance = await self._interpreter.interpret(guidance_text)
        print(render_guidance_interpreted(guidance))

        gov = self._governance.evaluate(guidance)
        if not gov.allowed:
            print(render_guidance_review(guidance, gov))
            if audit_trail:
                _dr = GuidanceApplicationResult(success=False, narrative_summary=f"Blocked: {gov.reason}")
                audit_trail.add(guidance, _dr, "blocked")
            return "escalated", None

        result = self._applier.apply(guidance, state)
        print(render_guidance_result(result))

        if audit_trail:
            audit_trail.add(guidance, result, "allowed")

        proposal = self._advisor.reassess(state)
        if proposal:
            print(f"\n  {_CYAN}New optimization opportunities after guidance:{_RESET}")
            print(render_optimization_proposal(proposal))

        return "guidance_applied", result
