from __future__ import annotations

from typing import Any

from freya.prompts.models import Prompt


class PromptRegistry:
    """In-memory store for reusable prompt templates."""

    def __init__(self) -> None:
        self._prompts: dict[str, Prompt] = {}

    def register(self, name: str, prompt: Prompt) -> None:
        """Register a prompt template under *name*.

        Raises ValueError if *name* is already registered.
        """
        if name in self._prompts:
            raise ValueError(f"Prompt '{name}' is already registered.")
        self._prompts[name] = prompt

    def get(self, name: str, variables: dict[str, Any] | None = None) -> Prompt:
        """Return a new Prompt instance with *variables* merged in.

        The original registered prompt is never mutated.
        Raises KeyError if *name* is not registered.
        """
        if name not in self._prompts:
            raise KeyError(f"Prompt '{name}' not found in registry.")
        original = self._prompts[name]
        merged_variables = {**original.variables, **(variables or {})}
        return Prompt(
            template=original.template,
            variables=merged_variables,
            system=original.system,
            metadata=original.metadata,
        )

    def list_prompts(self) -> list[str]:
        """Return the names of all registered prompts."""
        return list(self._prompts.keys())
