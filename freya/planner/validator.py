from __future__ import annotations

from dataclasses import dataclass, field

from freya.dag.models import DAG
from freya.dag.validation import DAGValidationError, validate_dag
from freya.registry import ToolRegistry


@dataclass
class PlannerValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


def validate_planner_dag(dag: DAG, tool_registry: ToolRegistry) -> PlannerValidationResult:
    """Validate a planner-generated DAG fragment.

    Checks:
    1. Structural correctness — no cycles, no missing dependency references.
    2. Tool existence — every tool task references a registered tool.
    3. Tool name presence — tool tasks must supply a non-empty tool_name.
    """
    errors: list[str] = []

    # 1. Structural validation
    try:
        validate_dag(dag)
    except DAGValidationError as exc:
        errors.append(str(exc))
        return PlannerValidationResult(valid=False, errors=errors)

    # 2 & 3. Tool existence and name presence
    for task in dag.tasks:
        if task.type == "tool":
            tool_name: str = task.input.get("tool_name", "")
            if not tool_name:
                errors.append(
                    f"Task '{task.task_id}' is a tool task but is missing 'tool_name'."
                )
                continue
            try:
                tool_registry.get(tool_name)
            except KeyError:
                errors.append(
                    f"Task '{task.task_id}' references unknown tool '{tool_name}'."
                )

    return PlannerValidationResult(valid=len(errors) == 0, errors=errors)
