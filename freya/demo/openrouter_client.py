"""OpenRouter LLM adapter using the OpenAI-compatible SDK."""
from __future__ import annotations

import os
from typing import Any, AsyncIterator

from openai import AsyncOpenAI, APIError, APITimeoutError


class OpenRouterAdapter:
    """OpenAI-compatible LLM adapter targeting the OpenRouter API.

    Usage::

        adapter = OpenRouterAdapter(model="anthropic/claude-3-haiku")
        response = await adapter.complete({"prompt": "...", "system": "..."})
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        timeout: float = 30.0,
        site_url: str = "https://github.com/pratikychavan/freya",
        site_name: str = "Freya SDK Demo",
    ) -> None:
        self._model = model
        self._timeout = timeout
        self._client = AsyncOpenAI(
            api_key=api_key or os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
            timeout=timeout,
            default_headers={
                "HTTP-Referer": site_url,
                "X-Title": site_name,
            },
        )

    @property
    def model(self) -> str:
        return self._model

    async def complete(self, request: dict[str, Any]) -> dict[str, Any]:
        prompt: str = request.get("prompt", "")
        system: str = request.get("system", "You are a helpful assistant.")

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
        except APITimeoutError as exc:
            raise RuntimeError(
                f"OpenRouter timeout after {self._timeout}s for model {self._model!r}"
            ) from exc
        except APIError as exc:
            raise RuntimeError(
                f"OpenRouter API error ({exc.status_code}): {exc.message}"
            ) from exc

        text: str = response.choices[0].message.content or ""
        usage: dict[str, int] = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return {"text": text, "usage": usage, "model": self._model}

    async def stream(self, request: dict[str, Any]) -> AsyncIterator[str]:
        raise NotImplementedError("Streaming not used in this demo.")

    def supports_vision(self) -> bool:
        return False

    def supports_tool_calls(self) -> bool:
        return False

    def token_budget(self) -> int:
        return 8_192
