from __future__ import annotations

from freya.workflows.coordinator import WorkflowCoordinator


def render_workflow_tree(
    coordinator: WorkflowCoordinator,
    session_id: str,
    show_contracts: bool = False,
) -> str:
    """Render the workflow subtree rooted at *session_id* as a text tree.

    When *show_contracts* is True, contract details are rendered as child lines
    beneath each node that has a registered ``DelegationContract``.

    Example output::

        planner-root
        ├── analyze_logs [contract: log-analysis-v1]
        │   ├── contract: log-analysis-v1
        │   ├── capabilities: summarize_logs
        │   └── success: produce incident summary
        └── classify_incident
    """
    lines: list[str] = [session_id]
    if show_contracts:
        _append_contract_lines(coordinator, session_id, prefix="", lines=lines)
    _render_children(coordinator, session_id, prefix="", lines=lines, show_contracts=show_contracts)
    return "\n".join(lines)


def _append_contract_lines(
    coordinator: WorkflowCoordinator,
    session_id: str,
    prefix: str,
    lines: list[str],
) -> None:
    """Append contract detail lines for *session_id* if a contract exists."""
    contract = coordinator.get_contract(session_id)
    if contract is None:
        return
    contract_id = getattr(contract, "contract_id", "unknown")[:8]
    caps = getattr(contract, "required_capabilities", [])
    criteria = getattr(contract, "success_criteria", [])
    reason = getattr(contract, "delegation_reason", "")
    lines.append(prefix + "    ├── contract: " + contract_id)
    if caps:
        lines.append(prefix + "    ├── capabilities: " + ", ".join(caps))
    if criteria:
        lines.append(prefix + "    ├── success: " + "; ".join(criteria))
    if reason:
        lines.append(prefix + "    └── reason: " + reason)


def _render_children(
    coordinator: WorkflowCoordinator,
    session_id: str,
    prefix: str,
    lines: list[str],
    show_contracts: bool = False,
) -> None:
    children = coordinator.get_children(session_id)
    for i, child_id in enumerate(children):
        is_last = i == len(children) - 1
        connector = "└── " if is_last else "├── "
        # Show contract id suffix in node label when available
        contract = coordinator.get_contract(child_id) if show_contracts else None
        contract_suffix = ""
        if contract is not None:
            contract_id = getattr(contract, "contract_id", "")[:8]
            contract_suffix = f" [contract: {contract_id}]"
        lines.append(prefix + connector + child_id + contract_suffix)
        child_prefix = prefix + ("    " if is_last else "│   ")
        if show_contracts:
            _append_contract_lines(coordinator, child_id, child_prefix, lines)
        _render_children(coordinator, child_id, child_prefix, lines, show_contracts=show_contracts)
