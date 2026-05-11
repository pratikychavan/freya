"""freya/context/store.py

Session-scoped operational context store.

Design rules:
  - Lightweight, in-process, deterministic
  - No vector store / no embeddings
  - Append-only history lists (auditable)
  - Context is keyed by workflow_id
  - Supports snapshot + restore (resumable state)
"""
from __future__ import annotations

from copy import deepcopy
from typing import Dict

from freya.context.models import OperationalContext, OperationalTrajectory


class OperationalContextStore:
    """Holds and updates OperationalContext objects keyed by workflow_id."""

    def __init__(self) -> None:
        self._contexts: Dict[str, OperationalContext] = {}
        self._trajectories: Dict[str, OperationalTrajectory] = {}

    # ── Context CRUD ────────────────────────────────────────────────────────

    def get(self, workflow_id: str) -> OperationalContext | None:
        return self._contexts.get(workflow_id)

    def get_or_create(self, workflow_id: str, **defaults) -> OperationalContext:
        if workflow_id not in self._contexts:
            self._contexts[workflow_id] = OperationalContext(
                workflow_id=workflow_id,
                workflow_state=defaults.get("workflow_state", "planning"),
            )
        return self._contexts[workflow_id]

    def save(self, ctx: OperationalContext) -> None:
        self._contexts[ctx.workflow_id] = ctx

    # ── History mutation helpers ─────────────────────────────────────────────

    def record_guidance(self, workflow_id: str, guidance: str) -> None:
        ctx = self.get_or_create(workflow_id)
        updated = ctx.model_copy(
            update={"prior_guidance": ctx.prior_guidance + [guidance]}
        )
        self.save(updated)

    def record_optimization(self, workflow_id: str, summary: str) -> None:
        ctx = self.get_or_create(workflow_id)
        updated = ctx.model_copy(
            update={"optimization_history": ctx.optimization_history + [summary]}
        )
        self.save(updated)

    def record_governance_event(self, workflow_id: str, summary: str) -> None:
        ctx = self.get_or_create(workflow_id)
        updated = ctx.model_copy(
            update={"governance_history": ctx.governance_history + [summary]}
        )
        self.save(updated)

    def update_mode(self, workflow_id: str, mode: str) -> None:
        ctx = self.get_or_create(workflow_id)
        self.save(ctx.model_copy(update={"operational_mode": mode}))

    def update_constraints(self, workflow_id: str, constraints: dict) -> None:
        ctx = self.get_or_create(workflow_id)
        merged = {**ctx.active_constraints, **constraints}
        self.save(ctx.model_copy(update={"active_constraints": merged}))

    def update_preferences(self, workflow_id: str, preferences: dict) -> None:
        ctx = self.get_or_create(workflow_id)
        merged = {**ctx.active_preferences, **preferences}
        self.save(ctx.model_copy(update={"active_preferences": merged}))

    # ── Trajectory ────────────────────────────────────────────────────────────

    def get_trajectory(self, workflow_id: str) -> OperationalTrajectory | None:
        return self._trajectories.get(workflow_id)

    def save_trajectory(self, traj: OperationalTrajectory) -> None:
        self._trajectories[traj.trajectory_id] = traj

    # ── Snapshot / restore ────────────────────────────────────────────────────

    def snapshot(self, workflow_id: str) -> dict:
        ctx = self._contexts.get(workflow_id)
        traj = self._trajectories.get(workflow_id)
        return {
            "context":    ctx.model_dump()  if ctx  else None,
            "trajectory": traj.model_dump() if traj else None,
        }

    def restore(self, snapshot: dict) -> None:
        if snapshot.get("context"):
            ctx = OperationalContext(**snapshot["context"])
            self._contexts[ctx.workflow_id] = ctx
        if snapshot.get("trajectory"):
            traj = OperationalTrajectory(**snapshot["trajectory"])
            self._trajectories[traj.trajectory_id] = traj

    def all_workflow_ids(self) -> list[str]:
        return list(self._contexts.keys())
