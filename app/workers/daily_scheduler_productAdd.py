from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import get_settings
from app.database import get_DataBase_mes
from app.timezone import get_timezone, taipei_now


logger = logging.getLogger(__name__)
_job_id = "daily_product_add_1230"
_scheduler: BackgroundScheduler | None = None

settings = get_settings()
# modelId source is fixed to this MES table by business rule.
SOURCE_TABLE = "mes.testmerge_cc1orcc2"
TARGET_TABLE = settings.PRODUCT_ADD_DATA_LOST_TABLE


@dataclass(frozen=True)
class QuerySpec:
    key: str
    table: str
    id_column: str
    fields: tuple[str, ...]
    extra_where_sql: str = ""
    field_suffix: str = ""


QUERY_SPECS: tuple[QuerySpec, ...] = (
    QuerySpec(
        key="assembly_batch",
        table="mes.assembly_batch",
        id_column="PLCCellID_CE",
        fields=("PARAM36", "PARAM37", "PARAM38", "PARAM39", "PARAM40", "PARAM44", "PARAM41", "PARAM07"),
    ),
    QuerySpec(
        key="schk_cellrule",
        table="mes.schk_cellrule",
        id_column="PLCCellID_CE",
        fields=("acirRP12_CE",),
    ),
    QuerySpec(
        key="testmerge_cc2",
        table="mes.testmerge_cc1orcc2",
        id_column="modelId",
        fields=("mOhm", "VAHSC", "OCV"),
        extra_where_sql="TRIM(`Para`) = 'CC2'",
    ),
    QuerySpec(
        key="testmerge_cc1",
        table="mes.testmerge_cc1orcc2",
        id_column="modelId",
        fields=("VAHSB",),
        extra_where_sql="TRIM(`Para`) = 'CC1'",
    ),
    QuerySpec(
        key="injection_batch_fin",
        table="mes.injection_batch_fin",
        id_column="PLCCellID_CE",
        fields=("Injection_batchNO", "nullWeight_CE", "packedWeight_CE"),
    ),
    QuerySpec(
        key="echk_batch",
        table="mes.echk_batch",
        id_column="PLCCellID_CE",
        fields=("PARAM18", "PARAM19", "PARAM02"),
        extra_where_sql="`PARAM01` = 3",
        field_suffix="_echk_batch",
    ),
    QuerySpec(
        key="echk2_batch",
        table="mes.echk2_batch",
        id_column="PLCCellID_CE",
        fields=("PARAM18", "PARAM19", "PARAM02"),
        extra_where_sql="`PARAM01` = 3",
        field_suffix="_echk2_batch",
    ),
    QuerySpec(
        key="cellinfo_v",
        table="cellinfo_v",
        id_column="PLCCellID_CE",
        fields=("cellthickness", "cellWeight"),
    ),
    QuerySpec(
        key="kvalueforprodinfo_update",
        table="mes.kvalueforprodinfo_update",
        id_column="cell",
        fields=("Kvalue",),
    ),
)

# 最終合併的資料結構範本，缺值以空字串表示。後續會根據這個範本來 upsert 到目標資料表。
NEW_DB_TEMPLATE: dict[str, Any] = {
    "modelId": "",
    "PARAM36": "",
    "PARAM37": "",
    "PARAM38": "",
    "PARAM39": "",
    "PARAM40": "",
    "PARAM44": "",
    "PARAM41": "",
    "PARAM07": "",
    "acirRP12_CE": "",
    "mOhm": "",
    "VAHSC": "",
    "OCV": "",
    "VAHSB": "",
    "Injection_batchNO": "",
    "nullWeight_CE": "",
    "packedWeight_CE": "",
    "PARAM18_echk_batch": "",
    "PARAM19_echk_batch": "",
    "PARAM02_echk_batch": "",
    "PARAM18_echk2_batch": "",
    "PARAM19_echk2_batch": "",
    "PARAM02_echk2_batch": "",
    "cellthickness": "",
    "cellWeight": "",
    "Kvalue": "",
    "systemFillIn_Time": "",
    "dataAllFillIn": "",
    "is_cleared": "0",
}


# 移除前後 空白字元
def _normalize_business_key(value: Any) -> str:
    return str(value or "").strip()

# 月份範圍從2023-01-01 到 現在
def _month_range(now: datetime) -> tuple[str, str]:
    raw_start = settings.PRODUCT_ADD_START_DATE.strip().replace("/", "-")
    start_date = datetime.fromisoformat(raw_start)
    start_dt = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        now.strftime("%Y-%m-%d %H:%M:%S"),
    )

# 批次撈取 modelId，避免一次撈太多造成記憶體爆掉
def _iter_model_id_batches(*, start_ts: str, end_ts: str, batch_size: int) -> Iterator[list[str]]:
    # Use keyset pagination to avoid long-lived streaming cursors that are prone to connection resets.
    page_size = max(batch_size * 4, 1000)
    max_retries = 3
    last_model_id = ""
    current_batch: list[str] = []
    engine = get_DataBase_mes()

    #先撈取現有的 modelId ，過濾掉已經 auto_full 的 modelId，減少後續處理量
    while True:
        sql = text(
            f"""
            SELECT modelId
            FROM (
                SELECT DISTINCT TRIM(modelId) AS modelId
                FROM {SOURCE_TABLE}
                WHERE analysisDT BETWEEN :start_ts AND :end_ts
                  AND modelId IS NOT NULL
                  AND TRIM(modelId) <> ''
                  AND TRIM(modelId) > :last_model_id
            ) src
            ORDER BY modelId
            LIMIT :page_size
            """
        )

        rows: list[dict[str, Any]] = []
        for attempt in range(max_retries + 1):
            try:
                with engine.connect() as conn:
                    rows = conn.execute(
                        sql,
                        {
                            "start_ts": start_ts,
                            "end_ts": end_ts,
                            "last_model_id": last_model_id,
                            "page_size": page_size,
                        },
                    ).mappings().all()
                break
            except OperationalError as exc:
                if attempt >= max_retries:
                    raise
                wait_s = attempt + 1
                logger.warning("modelId page fetch lost connection; retry %s/%s in %ss: %s", attempt + 1, max_retries, wait_s, exc)
                print(f"資料庫連線中斷，重試中({attempt + 1}/{max_retries})", flush=True)
                time.sleep(wait_s)

        if not rows:
            break

        for row in rows:
            
            modelId = row.get("modelId") or row.get("PLCCellID_CE") or row.get("cell")  # 根據不同的 QuerySpec 可能會有不同的欄位名稱
            model_id = _normalize_business_key(modelId)
            if not model_id:
                continue
            current_batch.append(model_id)
            last_model_id = model_id
            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []

    if current_batch:
        yield current_batch

# 根據 QuerySpec 的定義，將資料行轉換並合併到最終的資料結構中
def _apply_spec_row(spec: QuerySpec, row: dict[str, Any], out: dict[str, Any]) -> None:
    for field in spec.fields:
        target_key = f"{field}{spec.field_suffix}"
        out[target_key] = "" if row.get(field) is None else row.get(field)

# 根據 batch_ids 從資料庫撈取最新的資料，並根據 QUERY_SPECS 定義的規則合併成一個 dict
def _build_batch_params(batch_ids: list[str], *, prefix: str = "pid") -> tuple[str, dict[str, str]]:
    bind_names = [f"{prefix}_{idx}" for idx in range(len(batch_ids))]
    in_clause = ", ".join(f":{name}" for name in bind_names)
    params = {name: value for name, value in zip(bind_names, batch_ids, strict=False)}
    return in_clause, params

# 根據 batch_ids 從資料庫撈取最新的資料，並根據 QUERY_SPECS 定義的規則合併成一個 dict
def _fetch_latest_rows_by_spec(*, conn, spec: QuerySpec, batch_ids: list[str]) -> list[dict[str, Any]]:
    if not batch_ids:
        return []

    in_clause, params = _build_batch_params(batch_ids, prefix=f"{spec.key}_id")
    fields_projection = ", ".join(f"t.`{field}` AS `{field}`" for field in spec.fields)
    extra_where = f" AND {spec.extra_where_sql}" if spec.extra_where_sql else ""

    sql = text(
        f"""
        SELECT TRIM(t.`{spec.id_column}`) AS business_key, {fields_projection}
        FROM {spec.table} t
        INNER JOIN (
            SELECT TRIM(`{spec.id_column}`) AS business_key, MAX(id) AS max_id
            FROM {spec.table}
            WHERE TRIM(`{spec.id_column}`) IN ({in_clause}){extra_where}
            GROUP BY TRIM(`{spec.id_column}`)
        ) latest ON latest.max_id = t.id
        """
    )

    rows = conn.execute(sql, params).mappings().all()
    return [dict(row) for row in rows]


def _fetch_auto_full_model_ids(*, conn, batch_ids: list[str]) -> set[str]:
    if not batch_ids:
        return set()

    in_clause, params = _build_batch_params(batch_ids, prefix="target_id")
    sql = text(
        f"""
        SELECT TRIM(modelId) AS modelId
        FROM {TARGET_TABLE}
        WHERE TRIM(modelId) IN ({in_clause})
          AND dataAllFillIn = 'auto_full'
        """
    )
    rows = conn.execute(sql, params).mappings().all()
    return {_normalize_business_key(row.get("modelId")) for row in rows if row.get("modelId")}


def _fetch_existing_target_rows(*, conn, batch_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not batch_ids:
        return {}

    in_clause, params = _build_batch_params(batch_ids, prefix="target_row_id")
    select_cols = ", ".join(f"`{col}`" for col in NEW_DB_TEMPLATE.keys())
    sql = text(
        f"""
        SELECT {select_cols}
        FROM {TARGET_TABLE}
        WHERE TRIM(modelId) IN ({in_clause})
        """
    )
    rows = conn.execute(sql, params).mappings().all()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        model_id = _normalize_business_key(row.get("modelId"))
        if not model_id:
            continue
        out[model_id] = dict(row)
    return out


def _merge_with_existing_row(*, fresh: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
    if not existing:
        return fresh

    # Keep existing non-empty values when current source run has gaps.
    for col in NEW_DB_TEMPLATE.keys():
        if col in {"modelId", "systemFillIn_Time", "dataAllFillIn", "is_cleared"}:
            continue
        if fresh.get(col, "") == "":
            old_val = existing.get(col)
            if old_val is not None and str(old_val) != "":
                fresh[col] = old_val
    return fresh


def _collect_batch_data(*, batch_ids: list[str]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, bool]]]:
    merged_data = {batch_id: {**NEW_DB_TEMPLATE, "modelId": batch_id} for batch_id in batch_ids}
    query_hits = {
        batch_id: {spec.key: False for spec in QUERY_SPECS}
        for batch_id in batch_ids
    }

    engine = get_DataBase_mes()
    with engine.connect() as conn:
        for spec in QUERY_SPECS:
            rows = _fetch_latest_rows_by_spec(conn=conn, spec=spec, batch_ids=batch_ids)
            for row in rows:
                model_id = _normalize_business_key(row.get("business_key"))
                if not model_id or model_id not in merged_data:
                    continue
                _apply_spec_row(spec, row, merged_data[model_id])
                query_hits[model_id][spec.key] = True

    return merged_data, query_hits


def preview_product_data(*, product_id: str) -> dict[str, Any]:
    product_id = str(product_id).strip()
    if not product_id:
        return {"status": "error", "message": "product_id is required"}

    merged_by_id, query_hits_by_id = _collect_batch_data(batch_ids=[product_id])
    merged = merged_by_id[product_id]
    query_hits = query_hits_by_id[product_id]

    merged["systemFillIn_Time"] = taipei_now().strftime("%Y-%m-%d %H:%M:%S")
    missing_excludes = {"is_cleared", "dataAllFillIn", "systemFillIn_Time"}
    missing = [key for key, value in merged.items() if value == "" and key not in missing_excludes]
    merged["dataAllFillIn"] = "auto_missing" if missing else "auto_full"
    merged["is_cleared"] = "0" if missing else "1"

    return {
        "status": "ok",
        "productId": product_id,
        "query_hits": query_hits,
        "missing_fields": missing,
        "data": merged,
    }


def _upsert_payload(payload: list[dict[str, Any]], *, table_name: str) -> int:
    if not payload:
        return 0

    columns = list(NEW_DB_TEMPLATE.keys())
    col_clause = ", ".join(columns)
    val_clause = ", ".join(f":{col}" for col in columns)
    update_clause = ", ".join(
        f"{col}=VALUES({col})" for col in columns if col != "modelId"
    )
    sql = text(
        f"INSERT INTO {table_name} ({col_clause}) VALUES ({val_clause}) "
        f"ON DUPLICATE KEY UPDATE {update_clause}"
    )

    engine = get_DataBase_mes()
    with engine.begin() as conn:
        conn.execute(sql, payload)
    return len(payload)


# 主執行邏輯：撈取資料、合併、upsert 到目標資料表，並回傳處理結果統計資訊
def run_data_into_db(*, batch_size: int = 500, dry_run: bool = False, max_batches: int = 0) -> dict[str, Any]:

    now = taipei_now()
    start_ts = settings.PRODUCT_ADD_START_DATE.strip() + " 00:00:00"
    end_ts = now.strftime("%Y-%m-%d %H:%M:%S")
    logger.info("product-add job start: %s to %s", start_ts, end_ts)

    total_upserted = 0
    total_processed = 0
    total_batches = 0
    total_auto_missing = 0
    total_auto_full = 0
    total_skipped_auto_full = 0
    total_new_model_ids = 0
    missing_key_exclude = {"is_cleared", "dataAllFillIn", "systemFillIn_Time"}

    engine = get_DataBase_mes()
    has_any_batch = False

    # 第一步 批次撈取 modelId 並且過濾掉已經 auto_full 的 modelId，減少後續處理量
    for batch_ids in _iter_model_id_batches(start_ts=start_ts, end_ts=end_ts, batch_size=batch_size):
        has_any_batch = True
        if max_batches > 0 and total_batches >= max_batches:
            break

        with engine.connect() as conn:
            already_full_ids = _fetch_auto_full_model_ids(conn=conn, batch_ids=batch_ids)
            existing_rows = _fetch_existing_target_rows(conn=conn, batch_ids=batch_ids)
        pending_ids = [model_id for model_id in batch_ids if model_id not in already_full_ids]
        total_skipped_auto_full += len(batch_ids) - len(pending_ids)
        total_new_model_ids += sum(1 for model_id in batch_ids if model_id not in existing_rows)

        if not pending_ids:
            continue

        total_batches += 1
        merged_data, _ = _collect_batch_data(batch_ids=pending_ids)

        final_payload: list[dict[str, Any]] = []
        now_str = taipei_now().strftime("%Y-%m-%d %H:%M:%S")
        for model_id in pending_ids:
            row = merged_data.get(model_id)
            if not row:
                continue
            row = _merge_with_existing_row(fresh=row, existing=existing_rows.get(model_id))
            row["systemFillIn_Time"] = now_str

            missing = [
                key for key, value in row.items()
                if value == "" and key not in missing_key_exclude
            ]
            if missing:
                row["dataAllFillIn"] = "auto_missing"
                row["is_cleared"] = "0"
                total_auto_missing += 1
            else:
                row["dataAllFillIn"] = "auto_full"
                row["is_cleared"] = "1"
                total_auto_full += 1

            final_payload.append(row)

        total_processed += len(final_payload)
        if not dry_run:
            total_upserted += _upsert_payload(final_payload, table_name=TARGET_TABLE)

    if not has_any_batch:
        return {
            "status": "ok",
            "message": "No modelId in range",
            "window": {"start": start_ts, "end": end_ts},
            "processed": 0,
            "upserted": 0,
            "auto_missing_count": 0,
            "auto_full_count": 0,
            "skipped_auto_full_count": 0,
            "new_model_id_count": 0,
            "batches": 0,
            "dry_run": dry_run,
        }

    return {
        "status": "ok",
        "message": "Completed",
        "window": {"start": start_ts, "end": end_ts},
        "processed": total_processed,
        "upserted": total_upserted,
        "auto_missing_count": total_auto_missing,
        "auto_full_count": total_auto_full,
        "skipped_auto_full_count": total_skipped_auto_full,
        "new_model_id_count": total_new_model_ids,
        "batches": total_batches,
        "dry_run": dry_run,
    }


def run_product_add_job() -> dict[str, Any]:
    try:
        print("開始作業", flush=True)
        result = run_data_into_db(batch_size=settings.PRODUCT_ADD_BATCH_SIZE)
        logger.info("product-add job done: %s", result)
        return result
    except Exception as exc:  # pragma: no cover
        print(f"作業失敗: {exc}", flush=True)
        logger.exception("product-add job failed: %s", exc)
        return {"status": "error", "message": str(exc)}


def start_product_add_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    tz_name = settings.SCHEDULE_TIMEZONE
    hour = settings.PRODUCT_ADD_RUN_HOUR
    minute = settings.PRODUCT_ADD_RUN_MINUTE

    _scheduler = BackgroundScheduler(timezone=get_timezone(tz_name))
    _scheduler.add_job(
        run_product_add_job,
        CronTrigger(hour=hour, minute=minute, timezone=get_timezone(tz_name)),
        id=_job_id,
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("product-add scheduler started at %02d:%02d (%s)", hour, minute, tz_name)


def stop_product_add_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        _scheduler = None


def is_product_add_scheduler_running() -> bool:
    return bool(_scheduler and _scheduler.running)


def run_blocking_scheduler() -> None:
    tz_name = settings.SCHEDULE_TIMEZONE
    hour = settings.PRODUCT_ADD_RUN_HOUR
    minute = settings.PRODUCT_ADD_RUN_MINUTE

    scheduler = BlockingScheduler(timezone=get_timezone(tz_name))
    scheduler.add_job(
        run_product_add_job,
        CronTrigger(hour=hour, minute=minute, timezone=get_timezone(tz_name)),
        id=_job_id,
        replace_existing=True,
    )

    logger.info("blocking product-add scheduler running at %02d:%02d (%s)", hour, minute, tz_name)
    scheduler.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily product-add scheduler")
    parser.add_argument("--once", action="store_true", help="Run ETL once and exit")
    parser.add_argument("--dry-run", action="store_true", help="Do not write data to DB")
    parser.add_argument("--product-id", default="", help="Preview one productId and exit")
    parser.add_argument("--max-batches", type=int, default=0, help="Process only first N batches (0 = unlimited)")
    args = parser.parse_args()

    logging.basicConfig(
        level=settings.SCHEDULER_LOG_LEVEL,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    if args.product_id:
        result = preview_product_data(product_id=args.product_id)
        print(result)
        return

    if args.once:
        result = run_data_into_db(
            batch_size=settings.PRODUCT_ADD_BATCH_SIZE,
            dry_run=args.dry_run,
            max_batches=args.max_batches,
        )
        print(result)
        return

    run_blocking_scheduler()


if __name__ == "__main__":
    main()