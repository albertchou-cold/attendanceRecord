from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.config import get_settings
from app.database import create_db_and_tables
from app.workers.daily_scheduler_productAdd import start_product_add_scheduler
from app.workers.redis_listener import start_redis_listener, stop_redis_listener
from app.workers.rewarm_scheduler import start_rewarm_scheduler, stop_rewarm_scheduler
from app.workers.daily_scheduler_productAdd import stop_product_add_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
	settings = get_settings()
	create_db_and_tables()

	if settings.PRODUCT_ADD_SCHEDULER_ENABLED:
		start_product_add_scheduler()
	if settings.REWARM_SCHEDULER_ENABLED:
		start_rewarm_scheduler()
	if settings.REDIS_LISTENER_ENABLED:
		start_redis_listener()

	yield

	stop_product_add_scheduler()
	stop_rewarm_scheduler()
	stop_redis_listener()


def create_app() -> FastAPI:
	settings = get_settings()
	app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
	app.include_router(api_router, prefix=settings.API_V1_PREFIX)

	return app


app = create_app()