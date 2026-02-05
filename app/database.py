from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from app.models.base import BaseHR

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


_engine_hr: Engine | None = None


def get_engine_hr() -> Engine:
    global _engine_hr
    if _engine_hr is not None:
        return _engine_hr

    url = os.getenv("dataBase_hr")
    if not url:
        raise RuntimeError("Missing env var 'dataBase_hr' for HR database URL")

    _engine_hr = create_engine(
        url,
        echo=_env_bool("SQL_ECHO", False),
        pool_size=int(os.getenv("SQL_POOL_SIZE", "20")),
        max_overflow=int(os.getenv("SQL_MAX_OVERFLOW", "10")),
        pool_recycle=int(os.getenv("SQL_POOL_RECYCLE", "3600")),
    )
    return _engine_hr


def create_db_and_tables() -> None:
    # Ensure models are imported so SQLModel registers tables into metadata.
    from app.models.hr import hrDB as _hr_models  # noqa: F401

    BaseHR.metadata.create_all(get_engine_hr())


def get_session_hr() -> Generator[Session, None, None]:
    with Session(get_engine_hr()) as session:
        yield session
