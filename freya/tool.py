from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Type

from pydantic import BaseModel

if TYPE_CHECKING:
    from freya.context import ExecutionContext


class Tool(ABC):
    """Abstract base class for all tools.

    Subclasses must define:
        name         — unique tool identifier
        input_model  — Pydantic model used to validate raw input dicts
        output_model — Pydantic model used to validate execution output
    """

    name: ClassVar[str]
    input_model: ClassVar[Type[BaseModel]]
    output_model: ClassVar[Type[BaseModel]]

    @abstractmethod
    async def execute(self, input: BaseModel, context: "ExecutionContext") -> BaseModel: ...
