"""freya/topology/memory.py

Organizational Topology Memory Engine.

Stores and retrieves bounded historical operational patterns and
stabilization outcomes. All memory is operationally explainable —
no opaque ML-style weighting.
"""
from __future__ import annotations

from freya.topology.models import OperationalMemoryRecord

# ---------------------------------------------------------------------------
# Built-in memory catalog — represents organizational operational history.
# These records model known recurring pattern/outcome pairs.
# ---------------------------------------------------------------------------
_MEMORY_CATALOG: list[dict] = [
    {
        "pattern_key": "retry_amplification_after_governance_recovery",
        "historical_pattern": (
            "Retry amplification cluster emerges during governance recovery windows "
            "as held-back retries flush through the reasoning pool."
        ),
        "stabilization_outcome": "partial",
        "recovery_duration": "3–5 cycles when reactive; 1–2 cycles when pre-dampened.",
        "future_recommendation": (
            "Apply preventive coupling dampening between governance escalation and retry "
            "amplification partitions at the start of governance recovery — before retry "
            "pressure materializes."
        ),
    },
    {
        "pattern_key": "compression_increases_reprocessing",
        "historical_pattern": (
            "Aggressive reasoning compression decreases pool utilization initially but "
            "leads to increased reprocessing requests within 2–3 cycles due to shallower analysis."
        ),
        "stabilization_outcome": "partial",
        "recovery_duration": "2–3 additional cycles to clear reprocessing backlog.",
        "future_recommendation": (
            "Limit compression to 30% depth reduction. Monitor reprocessing rate as a "
            "leading indicator before applying further compression. Prefer batching first."
        ),
    },
    {
        "pattern_key": "delayed_reservations_worsen_recovery",
        "historical_pattern": (
            "Delayed capacity reservation during active retry amplification lengthened "
            "recovery by allowing contention to saturate without protected headroom."
        ),
        "stabilization_outcome": "failed",
        "recovery_duration": "5–8 cycles — significantly longer than pre-emptive reservation.",
        "future_recommendation": (
            "Activate proactive reservation at pressure ≥ 0.60 for critical workflows, "
            "before saturation occurs. Do not wait for contention to fully manifest."
        ),
    },
    {
        "pattern_key": "prolonged_batching_reduces_throughput",
        "historical_pattern": (
            "Governance batching sustained beyond 6 cycles began reducing overall approval "
            "throughput as batch windows caused latency accumulation for time-sensitive reviews."
        ),
        "stabilization_outcome": "partial",
        "recovery_duration": "Review cadence normalized within 2 cycles after batching taper.",
        "future_recommendation": (
            "Taper governance batching after 4 cycles regardless of pressure — schedule "
            "priority review windows to avoid latency accumulation before batching removal."
        ),
    },
    {
        "pattern_key": "optimization_recovery_increases_reasoning_pressure",
        "historical_pattern": (
            "Restoring optimization capacity before reasoning zone pressure dropped below 0.55 "
            "consistently triggered reasoning contention rebounds within 1–2 cycles."
        ),
        "stabilization_outcome": "failed",
        "recovery_duration": "Rebound resolved in 3–4 cycles; added delay vs staged approach.",
        "future_recommendation": (
            "Gate optimization restoration on reasoning pressure < 0.50. "
            "Restore at 20% increments per cycle with contention monitoring between each step."
        ),
    },
    {
        "pattern_key": "incident_coordination_post_resolution_governance_spike",
        "historical_pattern": (
            "Incident resolution consistently generated post-incident governance review demand, "
            "causing a governance escalation surge 1–2 cycles after incident closure."
        ),
        "stabilization_outcome": "effective",
        "recovery_duration": "Pre-positioned governance capacity absorbed spike within 1 cycle.",
        "future_recommendation": (
            "Pre-position expanded governance batching capacity 1 cycle before anticipated "
            "incident closure to absorb the post-resolution review surge proactively."
        ),
    },
    {
        "pattern_key": "chronic_smoothing_delays_recovery",
        "historical_pattern": (
            "Persistent smoothing beyond 8 cycles masked underlying contention instead of "
            "resolving root causes, delaying strategic recovery and increasing fatigue risk."
        ),
        "stabilization_outcome": "partial",
        "recovery_duration": "Full recovery extended by 4–6 cycles due to masked root cause.",
        "future_recommendation": (
            "Treat smoothing as a temporary bridge (≤ 5 cycles). Escalate to root-cause "
            "interventions (batching, reservation, sequencing) when smoothing persists beyond cycle 4."
        ),
    },
]


class OperationalTopologyMemoryEngine:
    """Retrieves historical operational memory records for known topology patterns."""

    def recall(self, pattern_key: str) -> OperationalMemoryRecord | None:
        """Return the memory record for a known pattern key, or None."""
        for entry in _MEMORY_CATALOG:
            if entry["pattern_key"] == pattern_key:
                return OperationalMemoryRecord(
                    historical_pattern=entry["historical_pattern"],
                    stabilization_outcome=entry["stabilization_outcome"],
                    recovery_duration=entry["recovery_duration"],
                    future_recommendation=entry["future_recommendation"],
                )
        return None

    def recall_all_for_context(
        self,
        active_signals: set[str],
        active_interventions: list[str],
    ) -> list[OperationalMemoryRecord]:
        """Return all memory records relevant to the current operational context.

        Simple keyword matching — bounded and fully transparent.
        """
        context_tokens = active_signals | set(active_interventions)
        relevance_map = {
            "retry_spike":                  ["retry_amplification_after_governance_recovery",
                                             "delayed_reservations_worsen_recovery"],
            "governance_congestion":        ["retry_amplification_after_governance_recovery",
                                             "prolonged_batching_reduces_throughput"],
            "batching_applied":             ["prolonged_batching_reduces_throughput"],
            "reasoning_compression":        ["compression_increases_reprocessing"],
            "smoothing_applied":            ["chronic_smoothing_delays_recovery"],
            "optimization_suspended":       ["optimization_recovery_increases_reasoning_pressure"],
            "escalation_active":            ["incident_coordination_post_resolution_governance_spike"],
            "recovery_surge":               ["incident_coordination_post_resolution_governance_spike"],
        }

        seen_keys: set[str] = set()
        records: list[OperationalMemoryRecord] = []
        for token in context_tokens:
            for key in relevance_map.get(token, []):
                if key in seen_keys:
                    continue
                record = self.recall(key)
                if record:
                    records.append(record)
                    seen_keys.add(key)
        return records

    def known_pattern_keys(self) -> list[str]:
        return [e["pattern_key"] for e in _MEMORY_CATALOG]
