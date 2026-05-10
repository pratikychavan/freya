"""freya/experience/models.py

Human-facing data models for the Experience Abstraction Layer.

These models translate internal runtime semantics into human-readable
structures. They are intentionally separate from runtime models so that
the experience layer can evolve independently.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class HumanProgressUpdate(BaseModel):
    """A single step of human-readable workflow progress."""

    title: str
    status: str  # "pending" | "running" | "done" | "warning" | "failed" | "paused"
    detail: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Status prefix glyphs for terminal rendering
    STATUS_GLYPHS: dict[str, str] = {
        "done":    "✓",
        "running": "⟳",
        "pending": "○",
        "warning": "⚠",
        "failed":  "✗",
        "paused":  "⏸",
    }

    def render(self) -> str:
        glyph = self.STATUS_GLYPHS.get(self.status, "·")
        line = f"  {glyph}  {self.title}"
        if self.detail:
            line += f"\n     {self.detail}"
        return line


class ApprovalExperience(BaseModel):
    """Human-readable approval checkpoint presented to the user."""

    title: str
    message: str
    impact_summary: str
    choices: list[str] = Field(default_factory=lambda: ["Approve", "Reject"])
    risk_level: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)  # carries raw data for callbacks

    def render(self) -> str:
        lines = [
            "",
            "  ┌────────────────────────────────────────────────────────────┐",
            f"  │  {self.title:<60}│",
            "  ├────────────────────────────────────────────────────────────┤",
        ]
        for para in self.message.splitlines():
            lines.append(f"  │  {para:<60}│")
        lines.append("  │" + " " * 62 + "│")
        for impact_line in self.impact_summary.splitlines():
            lines.append(f"  │  {impact_line:<60}│")
        lines.append("  │" + " " * 62 + "│")
        choices_str = "  ".join(f"[{c}]" for c in self.choices)
        lines.append(f"  │  {choices_str:<60}│")
        lines.append("  └────────────────────────────────────────────────────────────┘")
        return "\n".join(lines)


class NarrativeSummary(BaseModel):
    """Human-readable narrative summary of a completed workflow."""

    title: str
    summary: str
    highlights: list[str] = Field(default_factory=list)

    def render(self) -> str:
        lines = [f"  {self.title}", ""]
        lines.append(f"  {self.summary}")
        if self.highlights:
            lines.append("")
            for h in self.highlights:
                lines.append(f"    • {h}")
        return "\n".join(lines)


class SessionContinuityUpdate(BaseModel):
    """Human-readable lifecycle state message for session continuity."""

    message: str
    state: str  # "started" | "paused" | "resumed" | "restored" | "completed" | "failed"

    STATE_GLYPHS: dict[str, str] = {
        "started":   "▶",
        "paused":    "⏸",
        "resumed":   "▶",
        "restored":  "♻",
        "completed": "✅",
        "failed":    "✗",
    }

    def render(self) -> str:
        glyph = self.STATE_GLYPHS.get(self.state, "·")
        return f"  {glyph}  {self.message}"
