from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ToolCapability(BaseModel):
    """Runtime-introspected description of a single registered tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]

    def as_prompt_text(self) -> str:
        """Format this capability as a human-readable prompt block."""
        import json
        return (
            f"- {self.name}\n"
            f"  description: {self.description}\n"
            f"  input_schema: {json.dumps(self.input_schema, indent=2)}\n"
            f"  output_schema: {json.dumps(self.output_schema, indent=2)}"
        )
