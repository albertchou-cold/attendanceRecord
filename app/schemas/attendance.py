from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator



class AttendanceIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    userId: str
    userName: str | None = None
    positionarea: str | None = None
    station: str | None = None
    shift: str | None = None

    shiftDate: date | None = None
    firstIn: datetime | None = None
    lastOut: datetime | None = None
    status: str | None = None
    lastTimestamp: datetime | None = None

    shiftStartTime: time | None = None
    shiftEndTime: time | None = None

    @field_validator("shiftDate", mode="before")
    @classmethod
    def _parse_date(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

    @field_validator("shiftStartTime", "shiftEndTime", mode="before")
    @classmethod
    def _parse_time(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            return time.fromisoformat(v)
        return v

    @field_validator("firstIn", "lastOut", "lastTimestamp", mode="before")
    @classmethod
    def _parse_ts(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            ts = float(v)
            if ts > 1_000_000_000_000:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
        return v


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    userId: str
    userName: str | None
    positionarea: str | None
    station: str | None
    shift: str | None
    shiftDate: date | None
    firstIn: datetime | None
    lastOut: datetime | None
    status: str | None
    lastTimestamp: datetime | None
    shiftStartTime: time | None
    shiftEndTime: time | None
    created_at: datetime


class AttendanceStatusCheckIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    userId: str
    lastTimestamp: datetime | None = None


# 這個schema 用來rewarm emp的考勤狀態，會從hrDB的RecordAttendance裡面撈出排班
class AttendanceStatusRewarm(BaseModel):
    model_config = ConfigDict(extra="ignore")

    AssignScheduleName : str | None = None
    AssignScheduleID : str | None = None
    PositionArea : str | None = None
    Position : str | None = None
    EmployeeWorkTime : str | None = None
    SortWorkTimeStart : datetime | None = None
    SortWorkTimeEnd : datetime | None = None
    DeleteDateTime : datetime | None = None



# 這個schema 用來rewarm emp請假狀態 ，會從hrDB的RecordAttendance_leaveStartTime裡面撈出請假資訊
class AttendanceStatusRewarmLeave(BaseModel):
    model_config = ConfigDict(extra="ignore")

    employeeNumber : str | None = None
    employeeName : str | None = None
    leaveStartTime : datetime | None = None
    leaveEndTime : datetime | None = None
    errorStatusNotify : str | None = None
    authPosition : str | None = None
    


    
    

    
    
    