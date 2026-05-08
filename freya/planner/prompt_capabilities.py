from __future__ import annotations

from pydantic import BaseModel

from freya.planner.mode import PlanningMode


class PromptCapability(BaseModel):
    """Describes a reasoning/cognition operation available to the planner."""

    name: str
    purpose: str
    description: str
    required_inputs: list[str]
    output_description: str
    planning_mode: PlanningMode = PlanningMode.COGNITIVE

    def as_prompt_text(self) -> str:
        inputs = ", ".join(f'"{i}"' for i in self.required_inputs)
        return (
            f"- {self.name}\n"
            f"  purpose: {self.purpose}\n"
            f"  description: {self.description}\n"
            f"  required_inputs: [{inputs}]\n"
            f"  output: {self.output_description}"
        )
