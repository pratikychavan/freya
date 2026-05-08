from __future__ import annotations

from freya.workflows.contracts import DelegationContract


def validate_contract_capabilities(
    contract: DelegationContract,
    tool_registry: object,
    prompt_capability_registry: object | None = None,
) -> tuple[bool, list[str]]:
    """Check that all required capabilities in *contract* are available.

    Capability sources:
    - ``ToolRegistry.list_tools()``
    - ``PromptCapabilityRegistry.list_capabilities()`` (if provided)

    Returns a ``(valid, missing)`` tuple where *missing* is the list of
    capability names that could not be found in either registry.
    """
    available: set[str] = set()

    if tool_registry is not None:
        available.update(tool_registry.list_tools())  # type: ignore[attr-defined]

    if prompt_capability_registry is not None:
        try:
            caps = prompt_capability_registry.list_capabilities()  # type: ignore[attr-defined]
            available.update(c.name if hasattr(c, "name") else c for c in caps)
        except Exception:
            pass

    missing = [cap for cap in contract.required_capabilities if cap not in available]
    return len(missing) == 0, missing
