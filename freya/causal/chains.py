"""freya/causal/chains.py

OperationalCausalChainEngine

Builds bounded, auditable cause-and-effect chains for known operational
event types. All chains are grounded in operational telemetry — no
speculative reasoning.

Supported root event types:
  governance_congestion   → retry_amplification → reasoning_churn → degradation_risk
  retry_spike             → reasoning_pressure  → pool_exhaustion → contention
  degradation_onset       → quality_reduction   → reprocessing    → pressure_loop
  reservation_applied     → latency_improvement → recovery_speed  → equilibrium
  smoothing_applied       → gradual_compression → contention_drop → stability
  batching_applied        → interrupt_reduction → reasoning_calm  → equilibrium
"""
from __future__ import annotations

import uuid

from freya.causal.models import CausalPropagationChain, PropagationStrength

# ── Chain templates ────────────────────────────────────────────────────────────
# Each entry: root_event → (steps, projected_outcome, stabilization_effect, propagation_strength)

_CHAIN_TEMPLATES: dict[str, tuple[list[str], str, str, PropagationStrength]] = {
    "governance_congestion": (
        [
            "Governance approval queue grows beyond normal capacity.",
            "Pending approvals trigger repeated retry attempts by waiting workflows.",
            "Retry amplification increases reasoning pool utilization.",
            "Higher reasoning demand creates contention between concurrent workflows.",
            "Contention elevates operational pressure and risks degradation.",
        ],
        "Increased operational pressure; elevated degradation risk if unmitigated.",
        "none",
        "amplified",
    ),
    "retry_spike": (
        [
            "Workflow retry rate rises above baseline.",
            "Repeated execution consumes additional reasoning capacity.",
            "Reasoning pool utilization climbs toward saturation threshold.",
            "Pool exhaustion risk increases contention among active workflows.",
            "Coordinated workflows compete for the same limited capacity.",
        ],
        "Reasoning pool exhaustion risk; coordination contention likely.",
        "none",
        "amplified",
    ),
    "degradation_onset": (
        [
            "One or more workflows enter degraded operational mode.",
            "Reduced quality causes partial re-execution and reprocessing requests.",
            "Reprocessing demand adds to the existing reasoning load.",
            "Amplified load increases the likelihood of cascading degradation.",
            "Additional workflows may degrade, forming a pressure feedback loop.",
        ],
        "Cascading degradation risk; pressure feedback loop forming.",
        "none",
        "cascading",
    ),
    "reservation_applied": (
        [
            "Proactive capacity reservation protects critical workflow headroom.",
            "Critical workflows experience reduced latency under sustained pressure.",
            "Faster critical-workflow throughput reduces pending backlog.",
            "Lower backlog decreases retry frequency across the organization.",
            "Reduced retries dampen reasoning pressure and stabilize the pool.",
        ],
        "Improved equilibrium stability; critical workflow latency preserved.",
        "significant",
        "dampened",
    ),
    "smoothing_applied": (
        [
            "Gradual reasoning taper applied to background workflows.",
            "Progressive compression reduces peak reasoning demand incrementally.",
            "Lower peak demand prevents abrupt contention spikes.",
            "Reduced contention lowers retry probability for waiting workflows.",
            "Stabilized retry rate improves overall organizational equilibrium.",
        ],
        "Smoother operational continuity; contention dampening effective.",
        "significant",
        "dampened",
    ),
    "batching_applied": (
        [
            "Non-critical governance reviews aggregated into scheduled windows.",
            "Approval interruption frequency decreases for active workflows.",
            "Fewer interruptions reduce context-switching overhead in reasoning.",
            "Lower reasoning overhead reduces pool utilization volatility.",
            "Stable pool utilization lowers degradation risk and improves equilibrium.",
        ],
        "Improved equilibrium stability; governance bandwidth preserved.",
        "strong",
        "dampened",
    ),
    "optimization_suspended": (
        [
            "Background optimization passes suspended temporarily.",
            "Freed compute capacity redirected to active workflow execution.",
            "Active workflows experience lower latency under current load.",
            "Lower latency reduces timeout retries and execution churn.",
            "Reduced churn stabilizes the organizational reasoning pool.",
        ],
        "Short-term capacity freed; optimization quality deferred.",
        "partial",
        "neutral",
    ),
}

_CONFIDENCE_BY_STRENGTH: dict[PropagationStrength, float] = {
    "cascading": 0.85,
    "amplified": 0.80,
    "neutral":   0.70,
    "dampened":  0.75,
}


class OperationalCausalChainEngine:
    """Build annotated causal propagation chains from operational events."""

    def build(
        self,
        root_event_type: str,
        confidence_override: float | None = None,
    ) -> CausalPropagationChain:
        """Return the causal chain for a known root event type."""
        template = _CHAIN_TEMPLATES.get(root_event_type)
        if template is None:
            return self._unknown_chain(root_event_type)

        steps, outcome, stabilization, strength = template
        confidence = confidence_override or _CONFIDENCE_BY_STRENGTH.get(strength, 0.70)

        return CausalPropagationChain(
            chain_id=str(uuid.uuid4())[:8],
            root_event=root_event_type,
            propagation_steps=list(steps),
            projected_outcome=outcome,
            stabilization_effect=stabilization,  # type: ignore[arg-type]
            confidence_score=confidence,
            propagation_strength=strength,
        )

    def known_event_types(self) -> list[str]:
        return list(_CHAIN_TEMPLATES.keys())

    def chain_depth(self, chain: CausalPropagationChain) -> int:
        return len(chain.propagation_steps)

    # ── Private ────────────────────────────────────────────────────────────────

    @staticmethod
    def _unknown_chain(event_type: str) -> CausalPropagationChain:
        return CausalPropagationChain(
            chain_id=str(uuid.uuid4())[:8],
            root_event=event_type,
            propagation_steps=[
                f"Event '{event_type}' observed.",
                "Operational effect direction not yet characterized.",
                "Monitoring recommended pending further telemetry.",
            ],
            projected_outcome="Outcome uncertain — continued monitoring advised.",
            stabilization_effect="none",
            confidence_score=0.30,
            propagation_strength="neutral",
        )
