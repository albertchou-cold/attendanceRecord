from __future__ import annotations

from fastapi import APIRouter

from app.ai.schemas import AttendanceSummaryRequest
from app.ai.skills import AttendanceAnalyzer


router = APIRouter()


@router.get("/ai/health")
def ai_health() -> dict:
    return {"status": "ok"}


@router.post("/ai/skills/attendance-summary")
async def ai_attendance_summary(req: AttendanceSummaryRequest) -> dict:
    analyzer = AttendanceAnalyzer()
    result = await analyzer.summarize(user_id=req.user_id, status=req.status, note=req.note)
    return result.model_dump()
