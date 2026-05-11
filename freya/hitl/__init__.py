"""freya/hitl/__init__.py

Public API for the Advanced HITL (Human Operational Guidance) package.

The primary entry-point is ``GuidanceSession``, which wires together:
  - HumanGuidanceCLI      — terminal interaction
  - HumanGuidanceInterpreter — intent parsing (LLM + deterministic fallback)
  - HumanGuidanceGovernance  — policy enforcement
  - HumanGuidanceApplier     — safe state mutations
  - GuidanceAuditTrail       — immutable event history

Quick usage::

    session = GuidanceSession(state=state, session_id="bid-42")
    outcome, result = await session.run_checkpoint(
        context="Hotel Selection",
        reason="Cost exceeds budget by ₹8,000.",
        recommendation="Select a lower-tier hotel or adjust budget.",
    )
    print(session.audit_trail.render())
"""
from __future__ import annotations

import uuid
from typing import Literal

from freya.hitl.applier import HumanGuidanceApplier
from freya.hitl.cli import HITLOutcome, HumanGuidanceCLI, SimulatedGuidanceCLI
from freya.hitl.governance import HumanGuidanceGovernance
from freya.hitl.interpreter import HumanGuidanceInterpreter
from freya.hitl.models import (
    GuidanceApplicationResult,
    GuidanceAuditTrail,
    GuidanceGovernanceDecision,
    GuidanceHistoryEntry,
    GuidanceType,
    HumanGuidance,
)
from freya.hitl.rendering import (
    render_guidance_interpreted,
    render_guidance_prompt,
    render_guidance_result,
    render_guidance_review,
)
from freya.steering.models import WorkflowSteeringState


class GuidanceSession:
    """Full-pipeline HITL guidance session for one workflow checkpoint.

    Wraps CLI interaction, interpretation, governance, application, and auditing.
    For non-interactive / simulated scenarios, pass ``simulated=True`` and
    provide ``sim_choice`` + ``sim_guidance_text`` to ``run_checkpoint``.
    """

    def __init__(
        self,
        state: WorkflowSteeringState,
        session_id: str | None = None,
        llm_adapter: object | None = None,
    ) -> None:
        self._state = state
        self._session_id = session_id or str(uuid.uuid4())[:12]
        self._llm_adapter = llm_adapter
        self._trail = GuidanceAuditTrail(session_id=self._session_id)

    # ── Interactive (real terminal) ───────────────────────────────────

    def run_checkpoint_interactive(
        self,
        context: str,
        reason: str,
        recommendation: str | None = None,
    ) -> tuple[HITLOutcome, GuidanceApplicationResult | None]:
        """Blocking interactive checkpoint — reads from stdin."""
        cli = HumanGuidanceCLI(self._llm_adapter)
        outcome, result = cli.interact(
            state=self._state,
            context=context,
            reason=reason,
            current_recommendation=recommendation,
            audit_trail=self._trail,
        )
        return outcome, result

    # ── Simulated (demo / tests) ──────────────────────────────────────

    async def run_checkpoint(
        self,
        context: str,
        reason: str,
        recommendation: str | None = None,
        sim_choice: Literal["approve", "reject", "guidance"] = "approve",
        sim_guidance_text: str = "",
    ) -> tuple[HITLOutcome, GuidanceApplicationResult | None]:
        """Async non-interactive checkpoint for demos and tests.

        ``sim_choice`` and ``sim_guidance_text`` supply the simulated user input.
        """
        cli = SimulatedGuidanceCLI(self._llm_adapter)
        outcome, result = await cli.simulate(
            state=self._state,
            context=context,
            reason=reason,
            current_recommendation=recommendation,
            choice=sim_choice,
            guidance_text=sim_guidance_text,
            audit_trail=self._trail,
        )
        return outcome, result

    # ── Properties ───────────────────────────────────────────────────

    @property
    def audit_trail(self) -> GuidanceAuditTrail:
        return self._trail

    @property
    def state(self) -> WorkflowSteeringState:
        return self._state


__all__ = [
    # Session entry-point
    "GuidanceSession",
    # Models
    "HumanGuidance",
    "GuidanceApplicationResult",
    "GuidanceGovernanceDecision",
    "GuidanceHistoryEntry",
    "GuidanceAuditTrail",
    "GuidanceType",
    # Sub-system classes
    "HumanGuidanceCLI",
    "SimulatedGuidanceCLI",
    "HumanGuidanceInterpreter",
    "HumanGuidanceGovernance",
    "HumanGuidanceApplier",
    # Rendering helpers
    "render_guidance_prompt",
    "render_guidance_result",
    "render_guidance_review",
    "render_guidance_interpreted",
    # CLI type
    "HITLOutcome",
]
