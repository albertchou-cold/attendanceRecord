from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from app.config import get_settings
from app.models.base import BaseHR


_engine_hr: Engine | None = None
_engine_mes: Engine | None = None


def _build_connect_args(url: str, settings) -> dict[str, int | str]:
    if not url.lower().startswith("mysql"):
        return {}
    return {
        "connect_timeout": settings.SQL_CONNECT_TIMEOUT,
        "read_timeout": settings.SQL_READ_TIMEOUT,
        "write_timeout": settings.SQL_WRITE_TIMEOUT,
        "charset": "utf8mb4",
    }

def get_DataBase_mes() -> Engine: 
    global _engine_mes
    if _engine_mes is not None:
        return _engine_mes

    settings = get_settings()
    url = settings.dataBase_mes
    if not url:
        raise RuntimeError("Missing env var 'dataBase_mes' for MES database URL")

    _engine_mes = create_engine(
        url,
        echo=settings.SQL_ECHO,
        pool_size=settings.SQL_POOL_SIZE,
        max_overflow=settings.SQL_MAX_OVERFLOW,
        pool_recycle=settings.SQL_POOL_RECYCLE,
        pool_pre_ping=settings.SQL_POOL_PRE_PING,
        connect_args=_build_connect_args(url, settings),
    )
    return _engine_mes

def get_engine_hr() -> Engine:
    global _engine_hr
    if _engine_hr is not None:
        return _engine_hr

    settings = get_settings()
    url = settings.dataBase_hr
    if not url:
        raise RuntimeError("Missing env var 'dataBase_hr' for HR database URL")

    _engine_hr = create_engine(
        url,
        echo=settings.SQL_ECHO,
        pool_size=settings.SQL_POOL_SIZE,
        max_overflow=settings.SQL_MAX_OVERFLOW,
        pool_recycle=settings.SQL_POOL_RECYCLE,
        pool_pre_ping=settings.SQL_POOL_PRE_PING,
        connect_args=_build_connect_args(url, settings),
    )
    return _engine_hr


def create_db_and_tables() -> None:
    # Ensure models are imported so SQLModel registers tables into metadata.
    from app.models.hr import hrDB as _hr_models  # noqa: F401

    BaseHR.metadata.create_all(get_engine_hr())


def get_session_hr() -> Generator[Session, None, None]:
    with Session(get_engine_hr()) as session:
        yield session
