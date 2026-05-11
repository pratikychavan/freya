"""freya/intent/synthesizer.py

Converts a UserIntent into an executable WorkflowBlueprint.

The synthesizer:
  1. Looks up the best-matching WorkflowTemplate via the TEMPLATE_REGISTRY.
  2. Merges user constraints with template defaults.
  3. Constructs a natural-language ``synthesized_goal`` string that can be
     passed directly to ``IterativePlannerRunner.run()``.
  4. Selects which governance checks apply based on the constraint values.
"""
from __future__ import annotations

import re
from typing import Any

from freya.intent.models import UserIntent, WorkflowBlueprint
from freya.intent.templates import TEMPLATE_REGISTRY, WorkflowTemplate, get_template


class WorkflowSynthesizer:
    """Convert a UserIntent into a WorkflowBlueprint."""

    # Budget thresholds (INR) that trigger higher-tier governance
    _GOVERNANCE_BUDGET_THRESHOLD = 30_000
    _GOVERNANCE_HIGH_BUDGET = 75_000

    def synthesize(self, intent: UserIntent) -> WorkflowBlueprint:
        """Return a WorkflowBlueprint derived from *intent*."""
        template = self._resolve_template(intent)
        constraints = self._merge_constraints(intent, template)
        preferences = dict(intent.preferences)
        subworkflows = list(template.subworkflows) if template else self._generic_subworkflows(intent)
        governance = self._select_governance(intent, constraints, template)
        synthesized_goal = self._build_goal_string(intent, template, constraints)

        return WorkflowBlueprint(
            workflow_type=template.domain if template else (intent.inferred_domain or "generic"),
            primary_goal=intent.primary_goal,
            suggested_subworkflows=subworkflows,
            governance_requirements=governance,
            estimated_complexity=template.estimated_complexity if template else "moderate",
            recommended_strategy=template.recommended_strategy if template else "deterministic",
            synthesized_goal=synthesized_goal,
            constraints=constraints,
            preferences=preferences,
            template_id=template.template_id if template else None,
        )

    # ── Template resolution ───────────────────────────────────────────

    def _resolve_template(self, intent: UserIntent) -> WorkflowTemplate | None:
        if intent.inferred_domain:
            return get_template(intent.inferred_domain)
        # Try matching by keyword if classifier gave no domain
        for tmpl in TEMPLATE_REGISTRY.values():
            for tag in tmpl.tags:
                if tag.lower() in intent.raw_input.lower():
                    return tmpl
        return None

    # ── Constraint merging ────────────────────────────────────────────

    def _merge_constraints(
        self, intent: UserIntent, template: WorkflowTemplate | None
    ) -> dict[str, Any]:
        defaults = dict(template.constraint_defaults) if template else {}
        merged = {**defaults, **intent.constraints}   # user values override defaults
        return merged

    # ── Generic subworkflows when no template matches ─────────────────

    def _generic_subworkflows(self, intent: UserIntent) -> list[str]:
        goal = intent.primary_goal.lower()
        if "search" in goal or "find" in goal:
            return ["Search", "Evaluate Options", "Select Best", "Confirm"]
        return ["Analyse Request", "Plan Steps", "Execute", "Summarise"]

    # ── Governance selection ──────────────────────────────────────────

    def _select_governance(
        self,
        intent: UserIntent,
        constraints: dict[str, Any],
        template: WorkflowTemplate | None,
    ) -> list[str]:
        rules: list[str] = []
        if template:
            rules.extend(template.governance_requirements)

        budget = constraints.get("budget_inr", 0) or 0
        if budget > self._GOVERNANCE_HIGH_BUDGET:
            if "high_value_approval_required" not in rules:
                rules.append("high_value_approval_required")
        elif budget > self._GOVERNANCE_BUDGET_THRESHOLD:
            if "manager_approval_required" not in rules:
                rules.append("manager_approval_required")

        # Flag if no explicit budget provided — might overspend silently
        if not constraints.get("budget_inr"):
            if "cost_tracking_required" not in rules:
                rules.append("cost_tracking_required")

        return rules

    # ── Natural-language goal construction ────────────────────────────

    def _build_goal_string(
        self,
        intent: UserIntent,
        template: WorkflowTemplate | None,
        constraints: dict[str, Any],
    ) -> str:
        if template is None:
            return intent.primary_goal

        domain = template.domain

        if domain == "business_travel":
            return self._travel_goal(intent, constraints)
        if domain == "incident_response":
            return self._incident_goal(intent)
        if domain == "data_pipeline":
            return self._pipeline_goal(intent, constraints)
        if domain == "scheduling":
            return self._scheduling_goal(intent, constraints)
        if domain == "procurement":
            return self._procurement_goal(intent, constraints)
        return intent.primary_goal

    def _travel_goal(self, intent: UserIntent, c: dict) -> str:
        destination = next(
            (e for e in intent.extracted_entities
             if re.match(r"^[A-Z][a-z]", e)),
            None,
        )
        parts: list[str] = ["Plan a complete business trip"]
        if destination:
            parts[0] += f" to {destination}"
        if c.get("nights"):
            parts.append(f"for {c['nights']} nights")
        if c.get("budget_inr"):
            parts.append(f"within a budget of ₹{c['budget_inr']:,}")
        if intent.preferences.get("hotel_proximity"):
            parts.append("with a hotel near the venue")
        if intent.preferences.get("premium"):
            parts.append("preferring premium options")
        elif intent.preferences.get("budget_conscious"):
            parts.append("prioritising lowest cost")
        return " ".join(parts) + "."

    def _incident_goal(self, intent: UserIntent) -> str:
        desc = intent.raw_input[:100].strip().rstrip(".")
        return f"Coordinate incident response for: {desc}."

    def _pipeline_goal(self, intent: UserIntent, c: dict) -> str:
        src = c.get("source", "source system")
        dst = c.get("destination", "destination system")
        return f"Orchestrate a complete data pipeline from {src} to {dst}."

    def _scheduling_goal(self, intent: UserIntent, c: dict) -> str:
        attendees = c.get("attendees", "all attendees")
        duration = c.get("duration", "1 hour")
        return f"Schedule a {duration} meeting for {attendees}."

    def _procurement_goal(self, intent: UserIntent, c: dict) -> str:
        item = c.get("item", "requested item")
        qty = c.get("quantity", "required quantity")
        return f"Process procurement of {qty} × {item} from approved vendors."
