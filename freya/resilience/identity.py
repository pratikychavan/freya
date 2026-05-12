"""freya/resilience/identity.py

Organizational Identity Preservation Engine.

Detects drift in an organization's essential operating characteristics
and raises preservation signals before adaptation-induced distortion
becomes irreversible. Preserves HOW the organization operates — not
merely uptime or throughput.
"""
from __future__ import annotations

from freya.resilience.models import OrganizationalIdentityProfile, PreservationPriority


# ---------------------------------------------------------------------------
# Protected characteristics — the core identity signals Freya monitors.
# ---------------------------------------------------------------------------

PROTECTED_CHARACTERISTICS: list[str] = [
    "governance_rigor",
    "analytical_trustworthiness",
    "responsiveness",
    "recovery_quality",
    "operational_transparency",
]


# ---------------------------------------------------------------------------
# Degradation signal rules — each entry maps a condition to a signal label.
# Format: (intervention, min_cycles, signal, affected_characteristic)
# ---------------------------------------------------------------------------

_DEGRADATION_RULES: list[tuple[str, int, str, str]] = [
    ("compression",       4, "analytical_trust_erosion",         "analytical_trustworthiness"),
    ("compression",       6, "deep_analytical_trust_degradation", "analytical_trustworthiness"),
    ("batching",          5, "responsiveness_degradation",        "responsiveness"),
    ("batching",          7, "governance_throughput_impairment",  "governance_rigor"),
    ("smoothing",         4, "accountability_reduction",          "operational_transparency"),
    ("smoothing",         7, "transparency_masking",              "operational_transparency"),
    ("governance_review", 5, "governance_rigor_fatigue",          "governance_rigor"),
    ("reservation",       6, "recovery_flexibility_lock-in",      "recovery_quality"),
    ("recovery_sequencing", 6, "coordination_path_brittleness",  "recovery_quality"),
]


def _signals_for(active_interventions: dict[str, int]) -> list[str]:
    signals: list[str] = []
    for intervention, cycles in active_interventions.items():
        for rule_intervention, min_cycles, signal, _ in _DEGRADATION_RULES:
            if intervention == rule_intervention and cycles >= min_cycles:
                if signal not in signals:
                    signals.append(signal)
    return signals


def _affected_characteristics(signals: list[str]) -> list[str]:
    """Return the protected characteristics that are still intact given the Signal set."""
    degraded: set[str] = set()
    for intervention_name, min_cycles, signal, characteristic in _DEGRADATION_RULES:
        if signal in signals:
            degraded.add(characteristic)
    return [c for c in PROTECTED_CHARACTERISTICS if c not in degraded]


def _preservation_priority(signals: list[str]) -> PreservationPriority:
    critical_signals = {
        "deep_analytical_trust_degradation",
        "transparency_masking",
        "governance_throughput_impairment",
    }
    elevated_signals = {
        "analytical_trust_erosion",
        "governance_rigor_fatigue",
        "responsiveness_degradation",
        "accountability_reduction",
    }
    if any(s in critical_signals for s in signals):
        return "critical"
    if any(s in elevated_signals for s in signals):
        return "elevated"
    return "standard"


class OrganizationalIdentityPreservationEngine:
    """Monitors organizational identity drift and surfaces preservation signals."""

    def assess(
        self,
        active_interventions: dict[str, int],
    ) -> OrganizationalIdentityProfile:
        """Return an OrganizationalIdentityProfile for the current intervention state.

        Parameters
        ----------
        active_interventions:
            Mapping of intervention name → usage_cycles.
        """
        signals = _signals_for(active_interventions)
        intact_characteristics = _affected_characteristics(signals)
        priority = _preservation_priority(signals)

        return OrganizationalIdentityProfile(
            identity_name="Organizational Operating Identity",
            protected_characteristics=intact_characteristics,
            degradation_signals=signals,
            preservation_priority=priority,
        )

    def protected_characteristics(self) -> list[str]:
        """Return all characteristics that Freya monitors."""
        return list(PROTECTED_CHARACTERISTICS)

    def has_drift(self, profile: OrganizationalIdentityProfile) -> bool:
        """Return True if any degradation signals are active."""
        return len(profile.degradation_signals) > 0
