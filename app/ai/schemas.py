from __future__ import annotations

from pydantic import BaseModel


class AIResponse(BaseModel):
    provider: str
    model: str
    text: str


class AttendanceSummaryRequest(BaseModel):
    user_id: str
    status: str | None = None
    note: str | None = None
