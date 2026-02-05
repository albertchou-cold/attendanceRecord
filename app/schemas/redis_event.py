from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from pydantic import ConfigDict


class RedisStateChangeIn(BaseModel):
    key: str
    old_value: str | None = None
    new_value: str | None = None
    channel: str | None = None
    source: str = Field(default="web")
    created_at: datetime | None = None


class RedisStateChangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    old_value: str | None
    new_value: str | None
    channel: str | None
    source: str
    created_at: datetime