from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session

from app.database import get_engine_hr
from app.services.attendance import get_dbAttendance_Rewarm
from app.workers.redis_scv import get_redis_client


_scheduler: BackgroundScheduler | None = None


def _rewarm_job() -> None:
    redis_client = get_redis_client()
    with Session(get_engine_hr()) as session:
        get_dbAttendance_Rewarm(session=session, redis_client=redis_client)


def start_rewarm_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_rewarm_job, CronTrigger(hour=7, minute=0), id="rewarm_0700", replace_existing=True)
    _scheduler.add_job(_rewarm_job, CronTrigger(hour=19, minute=0), id="rewarm_1900", replace_existing=True)
    _scheduler.start()


def stop_rewarm_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        _scheduler = None
