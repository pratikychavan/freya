"""freya/org/policy.py

OrganizationalPolicyEngine

Applies domain-aware governance and operational rules per workflow domain.

Built-in policy profiles:
  - incident_response  : speed-first, minimal friction, deep reasoning
  - finance            : strict governance, conservative optimization
  - travel_operations  : flexible optimization, standard governance
  - executive_coordination: priority acceleration, elevated governance
  - security_operations: deep reasoning, strict governance, no auto-approve
  - research_analysis  : deep reasoning, minimal time pressure
  - default            : balanced
"""
from __future__ import annotations

from freya.org.models import GovernanceLevel, OrganizationalPolicy, PolicyProfile

# ── Built-in profiles ─────────────────────────────────────────────────────────
_PROFILES: dict[str, OrganizationalPolicy] = {
    "incident_response": OrganizationalPolicy(
        policy_name="Incident Response",
        workflow_domains=["incident", "incident_response", "outage", "emergency"],
        governance_level="flexible",
        execution_constraints={"max_reasoning_latency_ms": 500, "allow_fast_path": True},
        optimization_limits={"max_cost_increase_pct": 50, "quality_floor": "minimum"},
        reasoning_depth="deep",
        clarification_threshold=0.50,
        auto_approve=False,
        notes=["Speed-critical. Prioritize time-to-resolution above cost."],
    ),
    "finance": OrganizationalPolicy(
        policy_name="Finance",
        workflow_domains=["finance", "accounting", "budget", "payroll", "audit"],
        governance_level="strict",
        execution_constraints={"require_dual_approval": True, "audit_trail": True},
        optimization_limits={"max_cost_increase_pct": 5, "quality_floor": "high"},
        reasoning_depth="deep",
        clarification_threshold=0.85,
        auto_approve=False,
        notes=["Conservative optimization. All changes require governance sign-off."],
    ),
    "travel_operations": OrganizationalPolicy(
        policy_name="Travel Operations",
        workflow_domains=["travel", "booking", "hospitality", "trip"],
        governance_level="standard",
        execution_constraints={"budget_ceiling_inr": 50000},
        optimization_limits={"max_cost_reduction_pct": 30, "quality_floor": "standard"},
        reasoning_depth="standard",
        clarification_threshold=0.70,
        auto_approve=False,
        notes=["Flexible optimization within budget bounds."],
    ),
    "executive_coordination": OrganizationalPolicy(
        policy_name="Executive Coordination",
        workflow_domains=["executive", "board", "leadership", "c-suite"],
        governance_level="standard",
        execution_constraints={"priority_lane": True},
        optimization_limits={"max_cost_increase_pct": 20},
        reasoning_depth="deep",
        clarification_threshold=0.60,
        auto_approve=False,
        notes=["Priority execution lane. Elevated governance visibility."],
    ),
    "security_operations": OrganizationalPolicy(
        policy_name="Security Operations",
        workflow_domains=["security", "infosec", "threat", "vulnerability", "compliance"],
        governance_level="strict",
        execution_constraints={"require_approval": True, "log_all_decisions": True},
        optimization_limits={"no_speed_optimization": True},
        reasoning_depth="deep",
        clarification_threshold=0.90,
        auto_approve=False,
        notes=["Maximum governance. No shortcuts. Deep reasoning required."],
    ),
    "research_analysis": OrganizationalPolicy(
        policy_name="Research & Analysis",
        workflow_domains=["research", "analysis", "data", "reporting", "analytics"],
        governance_level="minimal",
        execution_constraints={"allow_long_running": True},
        optimization_limits={"max_cost_increase_pct": 10},
        reasoning_depth="deep",
        clarification_threshold=0.65,
        auto_approve=False,
        notes=["Deep reasoning preferred. Cost-tolerant for analytical accuracy."],
    ),
    "default": OrganizationalPolicy(
        policy_name="Default",
        workflow_domains=["*"],
        governance_level="standard",
        execution_constraints={},
        optimization_limits={},
        reasoning_depth="standard",
        clarification_threshold=0.70,
        auto_approve=False,
        notes=["Balanced operational defaults."],
    ),
}


class OrganizationalPolicyEngine:
    """Resolves and applies organizational policy for workflow domains."""

    def resolve(self, domain: str) -> OrganizationalPolicy:
        """Return the best-matching policy for a workflow domain string."""
        domain_lower = domain.lower()
        for profile_key, policy in _PROFILES.items():
            if profile_key == "default":
                continue
            if any(d in domain_lower for d in policy.workflow_domains):
                return policy
        return _PROFILES["default"]

    def resolve_by_profile(self, profile: PolicyProfile) -> OrganizationalPolicy:
        return _PROFILES.get(profile, _PROFILES["default"])

    def governance_strictness(self, policy: OrganizationalPolicy) -> int:
        """Return 0–4 numeric strictness for comparison."""
        return {"minimal": 0, "flexible": 1, "standard": 2, "strict": 3}.get(
            policy.governance_level, 2
        )

    def apply_to_clarification(
        self, policy: OrganizationalPolicy, base_confidence: float
    ) -> bool:
        """Return True if clarification should fire given org policy threshold."""
        return base_confidence < policy.clarification_threshold

    def describe(self, policy: OrganizationalPolicy) -> list[str]:
        """Human-readable policy summary lines."""
        lines = [
            f"Policy: {policy.policy_name}",
            f"Governance Level: {policy.governance_level}",
            f"Reasoning Depth: {policy.reasoning_depth}",
            f"Clarification Threshold: {int(policy.clarification_threshold * 100)}%",
            f"Auto-approve: {'Yes' if policy.auto_approve else 'No'}",
        ]
        if policy.notes:
            lines.extend(policy.notes)
        return lines

    def all_profiles(self) -> dict[str, OrganizationalPolicy]:
        return dict(_PROFILES)
