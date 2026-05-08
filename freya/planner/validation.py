from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from freya.dag.models import DAG
from freya.dag.validation import DAGValidationError, validate_dag
from freya.registry import ToolRegistry


class ValidationIssue(BaseModel):
    issue_type: str
    message: str
    task_id: str | None = None
    offending_value: str | None = None


class ValidationResult(BaseModel):
    valid: bool
    issues: list[ValidationIssue] = []

    def as_text(self) -> str:
        """Compact representation for planner repair prompts."""
        if self.valid:
            return "(valid)"
        return "\n".join(
            f"- [{i.issue_type}] {i.message}"
            + (f" (task: {i.task_id})" if i.task_id else "")
            + (f" (value: {i.offending_value})" if i.offending_value else "")
            for i in self.issues
        )


def validate_dag_fragment(
    dag: DAG,
    tool_registry: ToolRegistry,
    planning_context: Any | None = None,   # PlanningContext — passed for future hooks
) -> ValidationResult:
    """Validate a planner-generated DAG fragment before execution.

    Checks (in order):
    1. Schema / structural correctness — no duplicate task IDs, valid task types.
    2. Dependency validity — all depends_on references exist in the fragment.
    3. Cycle detection.
    4. Tool existence — tool tasks must reference a registered tool.
    5. Missing required fields — tool tasks need a non-empty tool_name;
       llm tasks need at least a prompt or prompt_name.
    """
    issues: list[ValidationIssue] = []

    # ── 1. Duplicate task IDs ────────────────────────────────────────────────
    seen_ids: set[str] = set()
    for task in dag.tasks:
        if task.task_id in seen_ids:
            issues.append(ValidationIssue(
                issue_type="DUPLICATE_TASK_ID",
                message=f"Duplicate task_id '{task.task_id}' found in DAG fragment.",
                task_id=task.task_id,
            ))
        seen_ids.add(task.task_id)

    # ── 2. Invalid task types ────────────────────────────────────────────────
    for task in dag.tasks:
        if task.type not in ("tool", "llm", "subworkflow"):
            issues.append(ValidationIssue(
                issue_type="INVALID_TASK_TYPE",
                message=f"Task type '{task.type}' is not supported. Must be 'tool', 'llm', or 'subworkflow'.",
                task_id=task.task_id,
                offending_value=task.type,
            ))

    # Early return — structural issues make further checks unreliable.
    if issues:
        return ValidationResult(valid=False, issues=issues)

    # ── 3. Dependency references + cycle detection (via validate_dag) ────────
    try:
        validate_dag(dag)
    except DAGValidationError as exc:
        issues.append(ValidationIssue(
            issue_type="DAG_STRUCTURE_ERROR",
            message=str(exc),
        ))
        return ValidationResult(valid=False, issues=issues)

    # ── 4. Tool existence + required fields ──────────────────────────────────
    for task in dag.tasks:
        if task.type == "tool":
            tool_name: str = task.input.get("tool_name", "")
            if not tool_name:
                issues.append(ValidationIssue(
                    issue_type="MISSING_TOOL_NAME",
                    message="Tool task is missing the required 'tool_name' field.",
                    task_id=task.task_id,
                ))
                continue
            try:
                tool_registry.get(tool_name)
            except KeyError:
                issues.append(ValidationIssue(
                    issue_type="UNKNOWN_TOOL",
                    message=f"Tool '{tool_name}' does not exist in the registry.",
                    task_id=task.task_id,
                    offending_value=tool_name,
                ))

        elif task.type == "llm":
            has_prompt = bool(task.input.get("prompt") or task.input.get("prompt_name"))
            if not has_prompt:
                issues.append(ValidationIssue(
                    issue_type="MISSING_PROMPT",
                    message="LLM task must supply either 'prompt' or 'prompt_name'.",
                    task_id=task.task_id,
                ))

        elif task.type == "subworkflow":
            if not task.input.get("goal"):
                issues.append(ValidationIssue(
                    issue_type="MISSING_SUBWORKFLOW_GOAL",
                    message="Subworkflow task must supply a non-empty 'goal' in input.",
                    task_id=task.task_id,
                ))

    return ValidationResult(valid=len(issues) == 0, issues=issues)
