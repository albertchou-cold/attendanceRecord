from __future__ import annotations

import json


from sqlmodel import Session, select

from app.models.hr.hrDB import (
    RecordAttendance_leaveStartTime,
    RecordAttendance_schedule_trackrecord,
)

from app.schemas.attendance import AttendanceStatusRewarm  # 撈排班資訊用的schema
from app.timezone import taipei_now

from datetime import datetime, timedelta


# python 的 rollback 機制 , 但主要是重新跑而已


def _shift_for_time(value: datetime) -> str:
    day_start = value.replace(hour=8, minute=0, second=0, microsecond=0)
    night_start = value.replace(hour=20, minute=0, second=0, microsecond=0)
    if day_start <= value < night_start:
        return "日班"
    return "夜班"


def _preload_window_shift(value: datetime) -> str:
    preload_day = value.replace(hour=7, minute=0, second=0, microsecond=0)
    preload_night = value.replace(hour=19, minute=0, second=0, microsecond=0)
    if preload_day <= value < preload_night:
        return "日班"
    return "夜班"


# 預先將資料塞進 redis 內（7:00 / 19:00 預熱）
def get_dbAttendance_Rewarm(*, session: Session, redis_client) -> list[AttendanceStatusRewarm]:
    now = taipei_now()
    shift = _preload_window_shift(now)

    schedule_rows = session.exec(
        select(RecordAttendance_schedule_trackrecord).where(
            RecordAttendance_schedule_trackrecord.EmployeeWorkTime == shift,
            (
                RecordAttendance_schedule_trackrecord.DeleteDateTime.is_(None)
                | (RecordAttendance_schedule_trackrecord.DeleteDateTime == "0000-00-00 00:00:00")
            ),
        )
    ).all()

    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = start_day + timedelta(days=1)
    leave_rows = session.exec(
        select(RecordAttendance_leaveStartTime).where(
            RecordAttendance_leaveStartTime.leaveStartTime >= start_day,
            RecordAttendance_leaveStartTime.leaveStartTime < end_day,
        )
    ).all()

    leave_employee_numbers = {
        row.employeeNumber
        for row in leave_rows
        if row.employeeNumber and _shift_for_time(row.leaveStartTime) == shift
    }

    filtered = [
        row
        for row in schedule_rows
        if row.EmployeeID not in leave_employee_numbers
    ]

    payloads: list[AttendanceStatusRewarm] = []
    for row in filtered:
        payload = AttendanceStatusRewarm.model_validate(row)
        payloads.append(payload)
        redis_client.set(
            f"user:status:{row.EmployeeID}",
            json.dumps({
                "userId": row.EmployeeID,
                "positionarea": row.PositionArea,
                "station": row.Position,
                "shift": shift,
                "warmAt": now.isoformat(),
                "isReWarmEmp": True,
            }),
        )

    cutoff = now - timedelta(days=1)
    for key in redis_client.keys("user:status:*"):
        raw = redis_client.get(key)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            warm_at = data.get("warmAt")
            if warm_at and datetime.fromisoformat(warm_at) < cutoff:
                redis_client.delete(key)
        except json.JSONDecodeError:
            continue

    return payloads


def get_attendance_status(*, redis_client, user_id: str) -> dict | None:
    raw = redis_client.get(f"user:status:{user_id}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"userId": user_id, "raw": raw}


def get_all_attendance_statuses(*, redis_client) -> list[dict]:
    keys = redis_client.keys("user:status:*")
    if not keys:
        return []

    results: list[dict] = []
    for key in keys:
        raw = redis_client.get(key)
        if not raw:
            continue
        try:
            results.append(json.loads(raw))
        except json.JSONDecodeError:
            user_id = key.split(":")[-1]
            results.append({"userId": user_id, "raw": raw})

    return results


def group_statuses_by_position_station(statuses: list[dict]) -> dict:
    grouped: dict[str, dict[str, list[dict]]] = {}
    for item in statuses:
        positionarea = str(item.get("positionarea") or "(unknown)")
        station = str(item.get("station") or "(unknown)")
        grouped.setdefault(positionarea, {}).setdefault(station, []).append(item)

    return grouped



def get_rewarm_emp_statuses(*, redis_client) -> list[dict]:
    statuses = get_all_attendance_statuses(redis_client=redis_client)
    return [status for status in statuses if status.get("isReWarmEmp")]
