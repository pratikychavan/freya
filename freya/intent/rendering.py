"""freya/intent/rendering.py

Terminal-friendly rendering of intent-layer objects.
Produces product-quality, non-technical output — no model field names,
no raw scores, no JSON blobs visible to users.
"""
from __future__ import annotations

from freya.intent.models import (
    ClarificationQuestion,
    IntentParseResult,
    UserIntent,
    WorkflowBlueprint,
)

# Glyphs / colour codes (ANSI)
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_MAGENTA = "\033[95m"
_RESET = "\033[0m"

_CHECK = "✓"
_CROSS = "✗"
_ARROW = "→"
_BULLET = "•"
_QUESTION = "❓"
_SPARK = "✦"
_BOX_H = "─"
_BOX_V = "│"
_BOX_TL = "╭"
_BOX_TR = "╮"
_BOX_BL = "╰"
_BOX_BR = "╯"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _box(title: str, width: int = 64) -> str:
    title_pad = f" {title} "
    pad_left = (width - 2 - len(title_pad)) // 2
    pad_right = width - 2 - len(title_pad) - pad_left
    top = _BOX_TL + _BOX_H * pad_left + title_pad + _BOX_H * pad_right + _BOX_TR
    return f"{_CYAN}{top}{_RESET}"


def _box_bottom(width: int = 64) -> str:
    return f"{_CYAN}{_BOX_BL}{_BOX_H * (width - 2)}{_BOX_BR}{_RESET}"


def _line(text: str = "", width: int = 64) -> str:
    inner = f" {text}" if text else ""
    padding = " " * (width - 2 - len(inner))
    return f"{_CYAN}{_BOX_V}{_RESET}{inner}{padding}{_CYAN}{_BOX_V}{_RESET}"


def _complexity_badge(level: str) -> str:
    colours = {"simple": _GREEN, "moderate": _YELLOW, "complex": _MAGENTA}
    c = colours.get(level, "")
    return f"{c}[{level.upper()}]{_RESET}"


def _strategy_badge(strat: str) -> str:
    labels = {
        "deterministic": ("DETERMINISTIC", _GREEN),
        "cognitive": ("COGNITIVE", _MAGENTA),
        "hybrid": ("HYBRID", _CYAN),
    }
    label, colour = labels.get(strat, (strat.upper(), ""))
    return f"{colour}[{label}]{_RESET}"


def _confidence_bar(score: float, width: int = 10) -> str:
    filled = int(round(score * width))
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {int(score * 100)}%"


# ---------------------------------------------------------------------------
# Public rendering functions
# ---------------------------------------------------------------------------


def render_intent_summary(intent: UserIntent, *, title: str = "Intent Understood") -> str:
    """Render a UserIntent in a human-friendly box."""
    lines: list[str] = [_box(title)]

    # Goal
    lines.append(f"{_BOLD}  Goal:{_RESET}  {intent.primary_goal}")

    # Domain
    domain_display = (intent.inferred_domain or "Unknown").replace("_", " ").title()
    lines.append(f"{_BOLD}  Domain:{_RESET} {domain_display}")

    # Confidence
    lines.append(f"{_BOLD}  Confidence:{_RESET} {_confidence_bar(intent.confidence)}")

    # Constraints
    if intent.constraints:
        lines.append("")
        lines.append(f"{_BOLD}  Constraints{_RESET}")
        for k, v in intent.constraints.items():
            label = k.replace("_", " ").title()
            if k == "budget_inr" and isinstance(v, (int, float)):
                value_str = f"₹{int(v):,}"
            else:
                value_str = str(v)
            lines.append(f"    {_BULLET} {label}: {value_str}")

    # Preferences
    if intent.preferences:
        lines.append("")
        lines.append(f"{_BOLD}  Preferences{_RESET}")
        for k, v in intent.preferences.items():
            if v:
                label = k.replace("_", " ").title()
                lines.append(f"    {_BULLET} {label}")

    # Entities
    if intent.extracted_entities:
        lines.append("")
        labels = ", ".join(intent.extracted_entities)
        lines.append(f"{_BOLD}  Detected Entities:{_RESET} {labels}")

    # Ambiguity notice
    if intent.requires_clarification:
        lines.append("")
        lines.append(f"  {_YELLOW}⚠  Some details are unclear and clarification is needed.{_RESET}")

    lines.append(_box_bottom())
    return "\n".join(lines)


def render_workflow_blueprint(blueprint: WorkflowBlueprint) -> str:
    """Render a WorkflowBlueprint with subworkflows, governance and strategy."""
    lines: list[str] = [_box("Workflow Blueprint")]

    # Synthesized goal
    lines.append(f"{_BOLD}  Synthesized Goal{_RESET}")
    lines.append(f"  {_ARROW} {blueprint.synthesized_goal}")
    lines.append("")

    # Complexity + strategy badges
    complexity = _complexity_badge(blueprint.estimated_complexity)
    strategy = _strategy_badge(blueprint.recommended_strategy)
    lines.append(f"  Complexity {complexity}    Strategy {strategy}")
    lines.append("")

    # Subworkflows
    if blueprint.suggested_subworkflows:
        lines.append(f"{_BOLD}  Planned Steps{_RESET}")
        for i, step in enumerate(blueprint.suggested_subworkflows, 1):
            lines.append(f"    {_DIM}{i}.{_RESET} {step}")
    lines.append("")

    # Applied constraints
    if blueprint.constraints:
        lines.append(f"{_BOLD}  Applied Constraints{_RESET}")
        for k, v in blueprint.constraints.items():
            label = k.replace("_", " ").title()
            if k == "budget_inr" and isinstance(v, (int, float)):
                v = f"₹{int(v):,}"
            lines.append(f"    {_BULLET} {label}: {v}")
        lines.append("")

    # Governance
    if blueprint.governance_requirements:
        lines.append(f"{_BOLD}  Governance{_RESET}")
        for req in blueprint.governance_requirements:
            label = req.replace("_", " ").title()
            lines.append(f"    {_YELLOW}⚑{_RESET} {label}")

    lines.append(_box_bottom())
    return "\n".join(lines)


def render_clarification_questions(questions: list[ClarificationQuestion]) -> str:
    """Render clarification questions in a compact, friendly format."""
    if not questions:
        return ""
    lines: list[str] = [_box("A Few Quick Questions")]
    for i, q in enumerate(questions, 1):
        lines.append(f"  {_QUESTION} {_BOLD}{i}.{_RESET} {q.question}")
        if q.options:
            opts = "  |  ".join(q.options)
            lines.append(f"      Options: {_DIM}{opts}{_RESET}")
    lines.append("")
    lines.append(f"  {_DIM}Please answer above to continue.{_RESET}")
    lines.append(_box_bottom())
    return "\n".join(lines)


def render_parse_result(result: IntentParseResult) -> str:
    """Render a complete IntentParseResult (summary + blueprint if ready)."""
    parts: list[str] = []

    parts.append(render_intent_summary(result.intent))
    parts.append("")

    if result.clarifications:
        parts.append(render_clarification_questions(result.clarifications))
    elif result.blueprint:
        parts.append(render_workflow_blueprint(result.blueprint))
        parts.append("")
        method = "AI-powered" if result.parse_method == "llm" else "pattern-based"
        parts.append(f"  {_DIM}{_SPARK} Intent parsed via {method} extraction.{_RESET}")

    return "\n".join(parts)
