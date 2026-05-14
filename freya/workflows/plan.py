"""freya/workflows/plan.py

WorkflowPlan and WorkflowPhase — the structured representation of an
objective decomposed into sequenced phases.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowPhase:
    """A single phase within a workflow plan."""
    name:                   str
    description:            str
    required_agent_domains: list[str]
    narration:              str = ""
    metadata:               dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name":                   self.name,
            "description":            self.description,
            "required_agent_domains": self.required_agent_domains,
            "narration":              self.narration,
        }


@dataclass
class WorkflowPlan:
    """
    Structured plan produced by WorkflowPlanner for one objective.

    Attributes:
        objective:             The original free-text objective.
        domain:                Primary operational domain (incident/migration/…).
        phases:                Ordered list of phases to execute.
        agents:                Agent domain names required overall.
        tools:                 Tool names required overall.
        missing_capabilities:  Capability gaps detected at planning time.
        risks:                 Human-readable risk statements.
        metadata:              Planner-specific annotations.
    """
    objective: str
    domain:    str
    phases:    list[WorkflowPhase]
    agents:    list[str] = field(default_factory=list)
    metadata:  dict[str, Any] = field(default_factory=dict)

    @property
    def phase_names(self) -> list[str]:
        return [p.name for p in self.phases]

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "domain":    self.domain,
            "phases":    [p.to_dict() for p in self.phases],
            "agents":    self.agents,
        }
