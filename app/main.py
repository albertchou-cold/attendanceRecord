from __future__ import annotations

import os

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.database import create_db_and_tables
from app.workers.redis_listener import start_redis_listener


def create_app() -> FastAPI:
	
	app = FastAPI(title="python_backend")
	app.include_router(api_router, prefix="/api/v1")

	@app.on_event("startup")
	def _startup() -> None:
		create_db_and_tables()
		if os.getenv("REDIS_LISTENER_ENABLED", "1").strip() not in {"0", "false", "False"}:
			start_redis_listener()

	return app


app = create_app()