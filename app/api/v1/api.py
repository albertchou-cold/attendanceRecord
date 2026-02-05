from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import attendance, health


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(attendance.router, tags=["attendance"])
