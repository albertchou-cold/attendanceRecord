from __future__ import annotations

from app.ai.providers import BaseAIProvider, MockAIProvider, OpenAIProvider
from app.ai.schemas import AIResponse
from app.config import get_settings


class AIService:
    def __init__(self, provider: BaseAIProvider) -> None:
        self.provider = provider

    async def complete(self, *, prompt: str, system_prompt: str = "") -> AIResponse:
        return await self.provider.complete(prompt=prompt, system_prompt=system_prompt)


def _build_provider() -> BaseAIProvider:
    settings = get_settings()
    provider = settings.AI_PROVIDER.strip().lower()
    if provider == "openai":
        return OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
    return MockAIProvider()


def get_ai_service() -> AIService:
    return AIService(_build_provider())
