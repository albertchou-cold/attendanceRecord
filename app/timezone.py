from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TAIPEI_TIMEZONE_NAME = "Asia/Taipei"
_TAIPEI_FALLBACK = timezone(timedelta(hours=8), name=TAIPEI_TIMEZONE_NAME)


def get_timezone(name: str = TAIPEI_TIMEZONE_NAME):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == TAIPEI_TIMEZONE_NAME:
            return _TAIPEI_FALLBACK
        raise


def taipei_now() -> datetime:
    return datetime.now(get_timezone())


def to_taipei(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(get_timezone())