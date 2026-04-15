from __future__ import annotations

from app.ai.providers.base import BaseAIProvider
from app.ai.schemas import AIResponse


class MockAIProvider(BaseAIProvider):
    async def complete(self, *, prompt: str, system_prompt: str = "") -> AIResponse:
        preview = prompt.strip().replace("\n", " ")[:200]
        return AIResponse(provider="mock", model="mock-v1", text=f"[mock] {preview}")
