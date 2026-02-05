from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.attendance import (
    get_all_attendance_statuses,
    get_attendance_status,
    get_rewarm_emp_statuses,
    group_statuses_by_position_station,
)
from app.workers.redis_scv import get_redis_client


router = APIRouter()




@router.get("/attendance/status/{user_id}")
def get_status(
    user_id: str,
    lastTimestamp: str | None = Query(default=None),
) -> dict:
    status = get_attendance_status(redis_client=get_redis_client(), user_id=user_id)
    if not status:
        return {"found": False, "changed": False, "data": None}

    changed = True
    if lastTimestamp:
        changed = str(status.get("lastTimestamp")) != lastTimestamp

    return {"found": True, "changed": changed, "data": status}


@router.get("/attendance/status")
def get_all_status() -> dict:
    statuses = get_all_attendance_statuses(redis_client=get_redis_client())
    return {"count": len(statuses), "data": statuses}


@router.get("/attendance/status/grouped")
def get_grouped_status() -> dict:
    statuses = get_all_attendance_statuses(redis_client=get_redis_client())
    grouped = group_statuses_by_position_station(statuses)
    return {"count": len(statuses), "data": grouped}


@router.get("/attendance/getReWarmEmp")
def get_rewarm_emp() -> dict:
    rewarm_emp = get_rewarm_emp_statuses(redis_client=get_redis_client())
    return {"count": len(rewarm_emp), "data": rewarm_emp}
