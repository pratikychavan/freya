"""freya/memory/capability.py

CapabilityMemory — stores workflow execution history and tool lineage
to support objective recall, playbook retrieval, and capability reuse.

Design:
  - In-memory store with optional persistence hooks
  - Similarity matching is keyword-based (no embeddings required)
  - All records are appended; nothing is mutated after storage
  - Domains and tool names are indexed for fast lookup
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkflowRecord:
    """Immutable record of a completed workflow execution."""
    record_id:    str
    objective:    str
    domain:       str
    plan_summary: dict[str, Any]
    outcome:      str   # "completed" | "failed"
    elapsed_ms:   float
    timestamp:    float
    tools_used:   tuple[str, ...]


@dataclass(frozen=True)
class ToolLineageRecord:
    """Records the provenance of a tool from proposal to activation."""
    tool_name:    str
    domain:       str
    proposed_at:  float
    approved_at:  float | None
    approved_by:  str | None
    rationale:    str
    risk_level:   str
    activated:    bool


@dataclass
class PlaybookEntry:
    """A reusable playbook derived from past workflow patterns."""
    name:        str
    domain:      str
    phases:      list[str]
    description: str
    used_count:  int = 0
    last_used:   float = field(default_factory=time.time)


class CapabilityMemory:
    """
    Stores workflow history, tool lineage, and reusable playbooks.

    Usage:
        mem = CapabilityMemory()
        mem.store_workflow(record_id="...", objective="...", domain="incident", ...)
        similar = mem.retrieve_similar_objectives("restore payment service")
        playbooks = mem.get_playbooks(domain="recovery")
    """

    def __init__(self) -> None:
        self._workflows:  list[WorkflowRecord] = []
        self._lineage:    list[ToolLineageRecord] = []
        self._playbooks:  list[PlaybookEntry] = []
        # Domain index: domain → list of indices in _workflows
        self._domain_idx: dict[str, list[int]] = {}

    # ------------------------------------------------------------------
    # Workflow history
    # ------------------------------------------------------------------

    def store_workflow(
        self,
        record_id: str,
        objective: str,
        domain: str,
        plan_summary: dict[str, Any],
        outcome: str,
        elapsed_ms: float,
        tools_used: list[str] | None = None,
    ) -> WorkflowRecord:
        record = WorkflowRecord(
            record_id=record_id,
            objective=objective,
            domain=domain,
            plan_summary=plan_summary,
            outcome=outcome,
            elapsed_ms=elapsed_ms,
            timestamp=time.time(),
            tools_used=tuple(tools_used or []),
        )
        idx = len(self._workflows)
        self._workflows.append(record)
        self._domain_idx.setdefault(domain, []).append(idx)
        self._update_playbook(record)
        return record

    def retrieve_similar_objectives(
        self,
        objective: str,
        top_k: int = 5,
    ) -> list[WorkflowRecord]:
        """
        Return up to top_k past workflows whose objective shares
        the most keywords with the given objective.
        """
        query_tokens = _tokenise(objective)
        if not query_tokens:
            return []

        scored: list[tuple[int, WorkflowRecord]] = []
        for record in self._workflows:
            record_tokens = _tokenise(record.objective)
            overlap = len(query_tokens & record_tokens)
            if overlap > 0:
                scored.append((overlap, record))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    # ------------------------------------------------------------------
    # Tool lineage
    # ------------------------------------------------------------------

    def store_tool_lineage(
        self,
        tool_name: str,
        domain: str,
        rationale: str,
        risk_level: str,
        approved_by: str | None = None,
        activated: bool = False,
    ) -> ToolLineageRecord:
        now = time.time()
        record = ToolLineageRecord(
            tool_name=tool_name,
            domain=domain,
            proposed_at=now,
            approved_at=now if approved_by else None,
            approved_by=approved_by,
            rationale=rationale,
            risk_level=risk_level,
            activated=activated,
        )
        self._lineage.append(record)
        return record

    def get_tool_lineage(self, tool_name: str) -> list[ToolLineageRecord]:
        return [r for r in self._lineage if r.tool_name == tool_name]

    # ------------------------------------------------------------------
    # Playbooks
    # ------------------------------------------------------------------

    def get_playbooks(self, domain: str | None = None) -> list[PlaybookEntry]:
        if domain is None:
            return list(self._playbooks)
        return [p for p in self._playbooks if p.domain == domain]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _update_playbook(self, record: WorkflowRecord) -> None:
        """Increment use count for matching playbook or create a new one."""
        for pb in self._playbooks:
            if pb.domain == record.domain:
                pb.used_count += 1
                pb.last_used = record.timestamp
                return

        phases = [p for p in record.plan_summary.get("phases", [])]
        self._playbooks.append(PlaybookEntry(
            name=f"{record.domain}_standard",
            domain=record.domain,
            phases=phases,
            description=f"Standard {record.domain} workflow playbook.",
            used_count=1,
            last_used=record.timestamp,
        ))


def _tokenise(text: str) -> set[str]:
    return {t for t in re.split(r'\W+', text.lower()) if len(t) > 2}
