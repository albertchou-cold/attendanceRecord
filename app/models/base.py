from __future__ import annotations

from sqlalchemy import MetaData
from sqlmodel import SQLModel


hr_metadata = MetaData()


class BaseHR(SQLModel):
	metadata = hr_metadata