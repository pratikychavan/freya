from __future__ import annotations

from freya.workflows.coordinator import WorkflowCoordinator


def render_workflow_tree(coordinator: WorkflowCoordinator, session_id: str) -> str:
    """Render the workflow subtree rooted at *session_id* as a text tree.

    Example output::

        planner-root
        ├── planner-root-child-1
        │   └── planner-root-child-1-recovery
        └── planner-root-child-2
    """
    lines: list[str] = [session_id]
    _render_children(coordinator, session_id, prefix="", lines=lines)
    return "\n".join(lines)


def _render_children(
    coordinator: WorkflowCoordinator,
    session_id: str,
    prefix: str,
    lines: list[str],
) -> None:
    children = coordinator.get_children(session_id)
    for i, child_id in enumerate(children):
        is_last = i == len(children) - 1
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + child_id)
        child_prefix = prefix + ("    " if is_last else "│   ")
        _render_children(coordinator, child_id, child_prefix, lines)
