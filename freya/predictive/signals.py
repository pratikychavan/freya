"""freya/predictive/signals.py

OperationalSignalEngine

Aggregates observed operational telemetry into directional signals.
Signals are operationally grounded — no speculative inference.

Tracked signals:
  - approval_latency        rising → governance congestion
  - retry_rate              rising → execution instability
  - optimization_queue      rising → optimization overload
  - escalation_frequency    rising → governance overload
  - degradation_usage       rising → reactive mode increasing
  - reasoning_pool_usage    rising → reasoning exhaustion approaching
  - workflow_surge_index    rising → more incident-type workflows active
"""
from __future__ import annotations

from freya.predictive.models import OperationalSignal, SignalDirection

# ── Default baselines ──────────────────────────────────────────────────────────
_BASELINES: dict[str, float] = {
    "approval_latency":     1.0,   # normalised minutes
    "retry_rate":           0.05,  # fraction 0–1
    "optimization_queue":   2.0,   # pending items
    "escalation_frequency": 0.1,   # per cycle
    "degradation_usage":    0.0,   # fraction of workflows degraded
    "reasoning_pool_usage": 0.50,  # fraction of pool consumed
    "workflow_surge_index": 1.0,   # multiplier vs baseline count
}

# Severity weight per unit of normalised deviation
_SEVERITY_WEIGHT: dict[str, float] = {
    "approval_latency":     0.30,
    "retry_rate":           0.40,
    "optimization_queue":   0.20,
    "escalation_frequency": 0.35,
    "degradation_usage":    0.45,
    "reasoning_pool_usage": 0.50,
    "workflow_surge_index": 0.25,
}

_DESCRIPTIONS: dict[str, str] = {
    "approval_latency":     "Time for governance approvals to be processed.",
    "retry_rate":           "Fraction of workflow steps requiring retries.",
    "optimization_queue":   "Number of pending optimization requests.",
    "escalation_frequency": "Rate of governance escalations per coordination cycle.",
    "degradation_usage":    "Fraction of workflows currently operating in a degraded mode.",
    "reasoning_pool_usage": "Proportion of shared reasoning capacity currently consumed.",
    "workflow_surge_index": "Relative surge in active incident/high-priority workflows.",
}


def _direction(current: float, baseline: float) -> SignalDirection:
    ratio = current / baseline if baseline > 0 else 1.0
    if ratio > 1.20:
        return "rising"
    if ratio < 0.80:
        return "falling"
    if abs(ratio - 1.0) <= 0.05:
        return "stable"
    return "volatile"


def _severity(signal_name: str, deviation: float) -> float:
    weight = _SEVERITY_WEIGHT.get(signal_name, 0.30)
    raw    = abs(deviation) * weight
    return min(raw, 1.0)


class OperationalSignalEngine:
    """Converts raw telemetry readings into structured directional signals."""

    def read(
        self,
        telemetry: dict[str, float],
        baselines: dict[str, float] | None = None,
    ) -> list[OperationalSignal]:
        """Convert a telemetry dict into a list of OperationalSignal objects."""
        effective_baselines = {**_BASELINES, **(baselines or {})}
        signals: list[OperationalSignal] = []

        for name, current in telemetry.items():
            baseline  = effective_baselines.get(name, current or 1.0)
            direction = _direction(current, baseline)
            deviation = ((current - baseline) / baseline) if baseline else 0.0
            severity  = _severity(name, deviation)

            signals.append(OperationalSignal(
                signal_name=name,
                current_value=current,
                baseline_value=baseline,
                direction=direction,
                severity=severity,
                description=_DESCRIPTIONS.get(name, f"Observed value for '{name}'."),
            ))

        return signals

    def aggregate_pressure(self, signals: list[OperationalSignal]) -> float:
        """Return an overall pressure score (0–1) from a set of signals."""
        if not signals:
            return 0.0
        total_severity = sum(s.severity for s in signals)
        return min(total_severity / len(signals), 1.0)

    def rising_signals(self, signals: list[OperationalSignal]) -> list[OperationalSignal]:
        return [s for s in signals if s.direction == "rising"]

    def critical_signals(
        self, signals: list[OperationalSignal], threshold: float = 0.65
    ) -> list[OperationalSignal]:
        return [s for s in signals if s.severity >= threshold]

    def describe(self, signals: list[OperationalSignal]) -> list[str]:
        lines = []
        for sig in sorted(signals, key=lambda s: s.severity, reverse=True):
            arrow = {"rising": "↑", "falling": "↓", "volatile": "~", "stable": "→"}.get(
                sig.direction, "→"
            )
            lines.append(
                f"{arrow} {sig.signal_name.replace('_', ' ').title()}: "
                f"{sig.current_value:.2f} (baseline {sig.baseline_value:.2f})"
                f" — severity {sig.severity:.0%}"
            )
        return lines
