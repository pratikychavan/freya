from __future__ import annotations

from typing import Any, AsyncIterator

from openai import AsyncOpenAI


class OpenAIAdapter:
    """Minimal OpenAI adapter — completion only (no streaming)."""

    def __init__(self, api_key: str | None = None, default_model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._default_model = default_model

    async def complete(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Expected request keys:
            prompt: str
            model:  str  (optional, falls back to default_model)
        Returns:
            text:   str
            usage:  dict
        """
        prompt: str = request["prompt"]
        model: str = request.get("model", self._default_model)

        response = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

        choice = response.choices[0]
        usage = response.usage

        return {
            "text": choice.message.content or "",
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
        }

    async def stream(self, request: dict[str, Any]) -> AsyncIterator[str]:
        prompt: str = request["prompt"]
        model: str = request.get("model", self._default_model)

        async def _gen() -> AsyncIterator[str]:
            async with self._client.chat.completions.stream(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        yield delta

        return _gen()

    def supports_vision(self) -> bool:
        return True

    def supports_tool_calls(self) -> bool:
        return True

    def token_budget(self) -> int:
        return 128_000
