from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "python_backend"
    API_V1_PREFIX: str = "/api/v1"

    dataBase_hr: str | None = None
    dataBase_mes: str | None = None
    SQL_ECHO: bool = False
    SQL_POOL_SIZE: int = 20
    SQL_MAX_OVERFLOW: int = 10
    SQL_POOL_RECYCLE: int = 3600
    SQL_POOL_PRE_PING: bool = True
    SQL_CONNECT_TIMEOUT: int = 10
    SQL_READ_TIMEOUT: int = 300
    SQL_WRITE_TIMEOUT: int = 300

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CHANNEL: str = "state_changes"
    REDIS_LISTENER_ENABLED: bool = True
    REDIS_SSL_INSECURE: bool = False

    PRODUCT_ADD_SCHEDULER_ENABLED: bool = True
    PRODUCT_ADD_RUN_HOUR: int = 15
    PRODUCT_ADD_RUN_MINUTE: int = 18
    PRODUCT_ADD_BATCH_SIZE: int = 500
    PRODUCT_ADD_START_DATE: str = "2023-01-01"
    PRODUCT_ADD_SOURCE_TABLE: str = "testmerge_cc1orcc2"
    PRODUCT_ADD_TARGET_TABLE: str = "daily_product_add"
    PRODUCT_ADD_DATA_LOST_TABLE: str = "dataLost_collection"
    PRODUCT_ADD_SKIP_AUTO_FULL: bool = True

    REWARM_SCHEDULER_ENABLED: bool = False
    SCHEDULE_TIMEZONE: str = "Asia/Taipei"
    SCHEDULER_LOG_LEVEL: str = "INFO"

    AI_PROVIDER: str = "mock"
    AI_DEFAULT_MODEL: str = "mock-v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"


@lru_cache
def get_settings() -> Settings:
    return Settings()
