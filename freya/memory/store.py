from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MemoryStore(ABC):
    @abstractmethod
    def get(self, session_id: str, key: str) -> Any | None: ...

    @abstractmethod
    def set(self, session_id: str, key: str, value: Any) -> None: ...

    @abstractmethod
    def delete(self, session_id: str, key: str) -> None: ...

    @abstractmethod
    def list_keys(self, session_id: str) -> list[str]: ...

    @abstractmethod
    def cleanup_session(self, session_id: str) -> None: ...


class InMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, session_id: str, key: str) -> Any | None:
        return self._store.get(session_id, {}).get(key)

    def set(self, session_id: str, key: str, value: Any) -> None:
        if session_id not in self._store:
            self._store[session_id] = {}
        self._store[session_id][key] = value

    def delete(self, session_id: str, key: str) -> None:
        self._store.get(session_id, {}).pop(key, None)

    def list_keys(self, session_id: str) -> list[str]:
        return list(self._store.get(session_id, {}).keys())

    def cleanup_session(self, session_id: str) -> None:
        self._store.pop(session_id, None)
