from __future__ import annotations

from abc import ABC, abstractmethod

from app.ai.schemas import AIResponse


class BaseAIProvider(ABC):
    @abstractmethod
    async def complete(self, *, prompt: str, system_prompt: str = "") -> AIResponse:
        raise NotImplementedError
