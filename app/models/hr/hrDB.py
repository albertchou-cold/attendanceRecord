from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseHR


def taipei_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Taipei"))

def to_taipei(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo("Asia/Taipei"))



# 排班資訊
class RecordAttendance_schedule_trackrecord(BaseHR, table=True):
    __tablename__ = "schedule_trackrecord"
    
    id: int | None = Field(default=None, primary_key=True)
    EmployeeName: str | None = Field(default=None)
    EmployeeID: str | None = Field(default=None)
    EmployeeEmail: str | None = Field(default=None)
    Password: str | None = Field(default=None)
    IsManager: int | None = Field(default=None)
    AssignScheduleName: str | None = Field(default=None)
    AssignScheduleID: str | None = Field(default=None)
    PositionArea: str | None = Field(default=None)
    Position: str | None = Field(default=None)
    EmployeeWorkTime: str | None = Field(default=None)
    SortWorkTimeStart: datetime | None = Field(default=None)
    SortWorkTimeEnd: datetime | None = Field(default=None)
    SubmitDateTime: datetime | None = Field(default=None)
    EditManagerName: str | None = Field(default=None)
    EditManagerID: str | None = Field(default=None)
    AdjustUpdateTime: datetime | None = Field(default=None)
    DeleteManagerName: str | None = Field(default=None)
    DeleteManagerID: str | None = Field(default=None)
    DeleteDateTime: datetime | None = Field(default=None)
    Random: str | None = Field(default=None)
    GroupI: str | None = Field(default=None)
    OverTimeWorking: str | None = Field(default=None)
    OnBoardTime: str | None = Field(default=None)
    Nationality: str | None = Field(default=None)
    Pattern: str | None = Field(default=None)
    Group_card_id: str | None = Field(default=None)
    Is_handmodify: int | None = Field(default=None)
    CountI: str | None = Field(default=None)
    Schedule_Time: datetime | None = Field(default=None)
    __table_args__ = (
        UniqueConstraint("AssignScheduleName", "AssignScheduleID", "SortWorkTimeStart", "Nationality", "Group_card_id", name="unique_four_fields"),
        UniqueConstraint("AssignScheduleName", "AssignScheduleID", "SortWorkTimeStart", name="unique_calendarProtect"),
    )


# 請假資訊
class RecordAttendance_leaveStartTime(BaseHR , table = True):
    __tablename__ = "absentsystem_leavesortoutall"

    id : int | None = Field(default=None, primary_key=True)
    workType : str = Field(default= "no", index = False)
    employeeNumber : str = Field(default= "no", index = True)
    employeeName : str = Field(default="no" , index = True)
    leaveType : str = Field(default="no" , index = False)
    leaveStartTime : datetime = Field(default_factory=taipei_now , index = True)
    leaveEndTime : datetime = Field(default_factory=taipei_now , index = True)
    leaveTotalHour : float = Field(default=0.0 , index = False)
    applyTime : datetime = Field(default_factory=taipei_now , index = False)
    managerSubmitTime : datetime = Field(default_factory=taipei_now , index = False)
    leaveFile : str = Field(default="no" , index = False)
    positionarea: dict = Field(default_factory=dict, sa_column=Column(JSON))
    describtion :str = Field(default="no" , index = False)
    errorStatusNotify : str = Field(default="3" , index = False)
    managerAuth : str = Field(default="0" , index = False)
    isManager : str = Field(default="no" , index = False)
    managerNumber : str = Field(default="no" , index = False)
    managerName : str = Field(default="no" , index = False)
    authPosition : dict = Field(default_factory=dict , sa_column=Column(JSON))
    apply_folder_link : str = Field(default="no" , index = False)
    is_synced : str = Field(default="0" , index = False)
    synced_at : datetime = Field(default_factory=taipei_now , index = False)
    randomuniqueid : str = Field(default="no" , index = True)
