"""freya/context/__init__.py

Contextual Operational Cognition layer.

Backwards-compatible: all existing `from freya.context import ExecutionContext`
imports continue to work because ExecutionContext is re-exported here.

New usage
---------
    from freya.context import ContextualCognitionPipeline, OperationalContextStore

    store = OperationalContextStore()
    pipeline = ContextualCognitionPipeline(store=store)
    result = await pipeline.process("Make it cheaper.", workflow_id="wf-001")
"""
from __future__ import annotations

# ── Backwards compatibility ───────────────────────────────────────────────────
from freya.context._execution_context import ExecutionContext  # noqa: F401

# ── New components ────────────────────────────────────────────────────────────
from typing import Callable, Awaitable

from freya.context.cognition import ContextualOperationalCognitionEngine
from freya.context.governance import ContextualGovernanceEngine, ContextualGovernanceDecision
from freya.context.history import WorkflowHistoryEngine
from freya.context.models import (
    ContextualClarificationHint,
    ContextualInterpretation,
    OperationalContext,
    OperationalTrajectory,
)
from freya.context.preferences import ContextualPreferenceEngine, InferredPreferences
from freya.context.rendering import (
    render_contextual_reasoning,
    render_drift_warnings,
    render_operational_context,
    render_operational_trajectory,
)
from freya.context.store import OperationalContextStore
from freya.context.trajectory import OperationalTrajectoryEngine

__all__ = [
    # Backwards compat
    "ExecutionContext",
    # Pipeline
    "ContextualCognitionPipeline",
    # Components
    "ContextualOperationalCognitionEngine",
    "ContextualGovernanceEngine",
    "WorkflowHistoryEngine",
    "OperationalTrajectoryEngine",
    "ContextualPreferenceEngine",
    "OperationalContextStore",
    # Models
    "OperationalContext",
    "ContextualInterpretation",
    "OperationalTrajectory",
    "ContextualClarificationHint",
    "ContextualGovernanceDecision",
    "InferredPreferences",
    # Renderers
    "render_operational_context",
    "render_contextual_reasoning",
    "render_operational_trajectory",
    "render_drift_warnings",
]

LLMAdapter = Callable[[dict], Awaitable[dict]]


class ContextualCognitionPipeline:
    """Façade that wires all contextual cognition components.

    Parameters
    ----------
    store:
        An OperationalContextStore instance (shared across calls for the same session).
    llm_adapter:
        Optional async callable ``(request: dict) -> dict``.
        If omitted, the pipeline operates fully deterministic.
    """

    def __init__(
        self,
        store: OperationalContextStore | None = None,
        llm_adapter: LLMAdapter | None = None,
    ) -> None:
        self.store       = store or OperationalContextStore()
        self._cognition  = ContextualOperationalCognitionEngine(llm_adapter=llm_adapter)
        self._governance = ContextualGovernanceEngine()
        self._history    = WorkflowHistoryEngine()
        self._trajectory = OperationalTrajectoryEngine()
        self._preferences= ContextualPreferenceEngine()

    # ── Primary interface ─────────────────────────────────────────────────────

    async def process(
        self,
        raw_input: str,
        workflow_id: str,
    ) -> dict:
        """Interpret raw_input in the context of the named workflow.

        Returns a dict with keys:
          - interpretation: ContextualInterpretation
          - governance:     ContextualGovernanceDecision
          - trajectory:     OperationalTrajectory
          - preferences:    InferredPreferences
          - instability:    list[str]          (warnings; empty = stable)
          - context:        OperationalContext (snapshot after recording guidance)
        """
        ctx = self.store.get_or_create(workflow_id)

        # 1. Contextual interpretation
        interpretation = await self._cognition.interpret(raw_input, ctx)

        # 2. Governance evaluation (contextual)
        decision = self._governance.evaluate(raw_input, ctx)

        # 3. Record guidance + governance outcome in store
        self.store.record_guidance(workflow_id, raw_input)
        if not decision.allowed:
            self.store.record_governance_event(
                workflow_id,
                f"Blocked [{decision.risk_level}]: \"{raw_input[:60]}\""
            )
        elif decision.scrutiny_level in ("elevated", "high", "maximum"):
            self.store.record_governance_event(
                workflow_id,
                f"Allowed under {decision.scrutiny_level} scrutiny: \"{raw_input[:60]}\""
            )

        # Refresh ctx after recording
        ctx = self.store.get_or_create(workflow_id)

        # 4. Trajectory
        trajectory = self._trajectory.compute(ctx)
        self.store.save_trajectory(trajectory)

        # 5. Instability detection
        instability = self._trajectory.detect_instability(ctx)

        # 6. Preference inference
        preferences = self._preferences.infer(ctx)

        return {
            "interpretation": interpretation,
            "governance":     decision,
            "trajectory":     trajectory,
            "preferences":    preferences,
            "instability":    instability,
            "context":        ctx,
        }

    def render(self, result: dict) -> str:
        """Produce a combined terminal display for a pipeline result dict."""
        parts: list[str] = [
            render_contextual_reasoning(result["interpretation"]),
            render_operational_trajectory(result["trajectory"]),
            render_operational_context(result["context"]),
        ]
        warnings = result.get("instability", [])
        if warnings:
            parts.append(render_drift_warnings(warnings))
        return "\n".join(parts)
