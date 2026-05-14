"""freya/workflows/node.py

WorkflowNode — a single executable unit in the workflow DAG.

Each node wraps a tool invocation or agent execution step. Nodes
declare their dependencies so WorkflowRuntime can resolve execution
order via the existing DAGRunner.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    SUCCEEDED = "succeeded"
    FAILED    = "failed"
    SKIPPED   = "skipped"
    BLOCKED   = "blocked"   # dependency failed


@dataclass
class WorkflowNode:
    """
    A single node in the workflow execution DAG.

    Attributes:
        node_id:      Unique identifier within the workflow.
        tool_name:    Name of the tool or agent domain to invoke.
        node_type:    "tool" or "agent"
        dependencies: node_ids this node waits for.
        input_data:   Resolved inputs passed at execution time.
        status:       Current execution status.
        retries:      Number of retry attempts made.
        max_retries:  Maximum retries before marking FAILED.
        output:       Captured execution output.
        error:        Last error message (if any).
        elapsed_ms:   Execution duration in milliseconds.
    """
    node_id:      str
    tool_name:    str
    node_type:    str = "tool"          # "tool" | "agent"
    dependencies: list[str] = field(default_factory=list)
    input_data:   dict[str, Any] = field(default_factory=dict)
    status:       NodeStatus = NodeStatus.PENDING
    retries:      int = 0
    max_retries:  int = 2
    output:       dict[str, Any] = field(default_factory=dict)
    error:        str = ""
    elapsed_ms:   float = 0.0

    @property
    def can_retry(self) -> bool:
        return self.retries < self.max_retries

    @property
    def terminal(self) -> bool:
        return self.status in (
            NodeStatus.SUCCEEDED,
            NodeStatus.FAILED,
            NodeStatus.SKIPPED,
        )

    def mark_running(self) -> None:
        self.status = NodeStatus.RUNNING

    def mark_succeeded(self, output: dict[str, Any], elapsed_ms: float) -> None:
        self.status = NodeStatus.SUCCEEDED
        self.output = output
        self.elapsed_ms = elapsed_ms

    def mark_failed(self, error: str, elapsed_ms: float = 0.0) -> None:
        self.status = NodeStatus.FAILED
        self.error = error
        self.elapsed_ms = elapsed_ms

    def mark_skipped(self, reason: str = "") -> None:
        self.status = NodeStatus.SKIPPED
        self.error = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id":      self.node_id,
            "tool_name":    self.tool_name,
            "node_type":    self.node_type,
            "dependencies": self.dependencies,
            "status":       self.status.value,
            "retries":      self.retries,
            "output":       self.output,
            "error":        self.error,
            "elapsed_ms":   self.elapsed_ms,
        }
