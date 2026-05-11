from __future__ import annotations

from dataclasses import dataclass

from freya.memory.store import MemoryStore


@dataclass
class ExecutionContext:
    session_id: str
    task_id: str
    memory: MemoryStore
