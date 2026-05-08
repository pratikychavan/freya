from __future__ import annotations

from freya import Prompt, PromptRegistry


def build_prompt_registry() -> PromptRegistry:
    pr = PromptRegistry()

    pr.register(
        "expense_approval_request",
        Prompt(
            template=(
                "Review the following expense report and decide whether to approve it.\n\n"
                "{report}\n\n"
                "Total: ${total:.2f}\n"
                "Respond with APPROVED or NEEDS_REVIEW, followed by a one-line reason."
            ),
            system="You are a strict but fair finance approval assistant.",
            metadata={"category": "finance", "version": 1},
        ),
    )

    pr.register(
        "expense_summary",
        Prompt(
            template=(
                "Summarise this expense report in one sentence for a manager's digest:\n\n"
                "{report}"
            ),
            system="You are a concise business writing assistant.",
            metadata={"category": "finance", "version": 1},
        ),
    )

    return pr