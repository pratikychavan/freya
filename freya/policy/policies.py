from __future__ import annotations

from typing import Any

from freya.policy.base import Policy, PolicyResult


class MaxLengthPolicy(Policy):
    """Blocks LLM tasks whose prompt exceeds a character threshold."""

    def __init__(self, max_chars: int = 1000) -> None:
        self.max_chars = max_chars

    def check_input(self, task: dict[str, Any], context: dict[str, Any]) -> PolicyResult:
        if context.get("task_type") != "llm":
            return PolicyResult(action="ALLOW")
        prompt = task.get("input", {}).get("prompt", "")
        if len(prompt) > self.max_chars:
            return PolicyResult(
                action="BLOCK",
                reason=f"Prompt length {len(prompt)} exceeds max {self.max_chars} chars.",
            )
        return PolicyResult(action="ALLOW")

    def check_output(
        self, task: dict[str, Any], result: dict[str, Any], context: dict[str, Any]
    ) -> PolicyResult:
        return PolicyResult(action="ALLOW")


class RequiredFieldPolicy(Policy):
    """Blocks tool tasks that are missing required keys in tool_input."""

    def __init__(self, required_fields: list[str]) -> None:
        self.required_fields = required_fields

    def check_input(self, task: dict[str, Any], context: dict[str, Any]) -> PolicyResult:
        if context.get("task_type") != "tool":
            return PolicyResult(action="ALLOW")
        tool_input: dict[str, Any] = task.get("input", {}).get("tool_input", {})
        missing = [f for f in self.required_fields if f not in tool_input]
        if missing:
            return PolicyResult(
                action="BLOCK",
                reason=f"Missing required fields in tool_input: {missing}",
            )
        return PolicyResult(action="ALLOW")

    def check_output(
        self, task: dict[str, Any], result: dict[str, Any], context: dict[str, Any]
    ) -> PolicyResult:
        return PolicyResult(action="ALLOW")


class PromptKeywordPolicy(Policy):
    """Warns when a prompt contains a flagged keyword (demonstrates WARN path)."""

    def __init__(self, keywords: list[str]) -> None:
        self.keywords = [kw.lower() for kw in keywords]

    def check_input(self, task: dict[str, Any], context: dict[str, Any]) -> PolicyResult:
        if context.get("task_type") != "llm":
            return PolicyResult(action="ALLOW")
        prompt: str = task.get("input", {}).get("prompt", "").lower()
        hit = next((kw for kw in self.keywords if kw in prompt), None)
        if hit:
            return PolicyResult(action="WARN", reason=f"Prompt contains flagged keyword: '{hit}'")
        return PolicyResult(action="ALLOW")

    def check_output(
        self, task: dict[str, Any], result: dict[str, Any], context: dict[str, Any]
    ) -> PolicyResult:
        return PolicyResult(action="ALLOW")
