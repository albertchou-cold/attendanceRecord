from __future__ import annotations

from app.ai.providers.base import BaseAIProvider
from app.ai.schemas import AIResponse


class OpenAIProvider(BaseAIProvider):
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def complete(self, *, prompt: str, system_prompt: str = "") -> AIResponse:
        # Reserved integration point for OpenAI SDK.
        # Keep the project install-light by not forcing openai package in base requirements.
        text = "OpenAI provider placeholder. Install optional AI dependencies and implement SDK call here."
        return AIResponse(provider="openai", model=self.model, text=text)
