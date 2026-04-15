from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import ai, attendance, health, product_add


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(attendance.router, tags=["attendance"])
api_router.include_router(product_add.router, tags=["product-add"])
api_router.include_router(ai.router, tags=["ai"])
