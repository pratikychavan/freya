from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Prompt(BaseModel):
    template: str
    variables: dict[str, Any] = {}
    system: str | None = None
    metadata: dict[str, Any] = {}

    def render(self) -> str:
        """Render the template by substituting all variables."""
        try:
            return self.template.format(**self.variables)
        except KeyError as exc:
            raise ValueError(f"Missing variable {exc} required by prompt template") from exc
