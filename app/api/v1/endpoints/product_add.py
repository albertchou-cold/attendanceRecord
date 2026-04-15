from __future__ import annotations

from fastapi import APIRouter, Query

from app.workers.daily_scheduler_productAdd import (
    is_product_add_scheduler_running,
    preview_product_data,
    run_data_into_db,
)


router = APIRouter()


@router.post("/product-add/run")
def run_product_add(
    dry_run: bool = Query(default=True, description="If true, only validate and do not write"),
    batch_size: int = Query(default=500, ge=1, le=5000),
) -> dict:
    return run_data_into_db(batch_size=batch_size, dry_run=dry_run)


@router.get("/product-add/preview/{product_id}")
def preview_product_add(product_id: str) -> dict:
    return preview_product_data(product_id=product_id)


@router.get("/product-add/scheduler/status")
def product_add_scheduler_status() -> dict:
    return {"running": is_product_add_scheduler_running()}