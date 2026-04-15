from __future__ import annotations

from app.ai.schemas import AIResponse
from app.ai.service import get_ai_service


class AttendanceAnalyzer:
    async def summarize(self, *, user_id: str, status: str | None, note: str | None) -> AIResponse:
        service = get_ai_service()
        prompt = (
            "Summarize attendance risk and recommendation.\n"
            f"user_id={user_id}\n"
            f"status={status or 'unknown'}\n"
            f"note={note or ''}"
        )
        return await service.complete(prompt=prompt, system_prompt="You are an attendance assistant.")
