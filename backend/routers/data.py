"""数据中心同步和基础行情查询路由。"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.core.response import error_response, success_response
from backend.db.session import SessionLocal, get_db
from backend.models.market import KlineDaily, SecurityInfo
from backend.services.data_center.sync_engine import data_sync_engine

router = APIRouter(prefix="/api/v1", tags=["data"])


def _json_value(value: Any) -> Any:
    """将 Decimal/date/datetime 等数据库字段转换为 JSON 友好的值。"""

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _run_mock_sync_in_background() -> None:
    """后台任务内部创建并关闭独立数据库 Session。"""

    db = SessionLocal()
    try:
        data_sync_engine.start_mock_sync(db)
    finally:
        db.close()


@router.post("/data/sync/start")
def start_data_sync(background_tasks: BackgroundTasks) -> dict:
    """启动 mock 数据同步任务，使用后台任务避免阻塞请求。"""

    if not data_sync_engine.mark_started():
        logger.info("Mock data sync start rejected because another task is running")
        return error_response(message="已有同步任务正在运行", data=data_sync_engine.get_status())

    background_tasks.add_task(_run_mock_sync_in_background)
    logger.info("Mock data sync background task submitted")
    return success_response(message="mock 数据同步任务已启动", data=data_sync_engine.get_status())


@router.get("/data/sync/status")
def get_data_sync_status() -> dict:
    """查询数据同步任务当前进度。"""

    return success_response(message="数据同步状态查询成功", data=data_sync_engine.get_status())


@router.get("/securities")
def list_securities(
    asset_type: str | None = Query(default=None, description="资产类型，例如 ETF/STOCK"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    """查询证券基础信息，支持按资产类型过滤。"""

    try:
        statement = select(SecurityInfo).order_by(SecurityInfo.symbol).limit(limit)
        if asset_type:
            statement = (
                select(SecurityInfo)
                .where(SecurityInfo.asset_type == asset_type)
                .order_by(SecurityInfo.symbol)
                .limit(limit)
            )
        securities = db.execute(statement).scalars().all()
        data = [
            {
                "id": security.id,
                "symbol": security.symbol,
                "name": security.name,
                "exchange": security.exchange,
                "asset_type": security.asset_type,
                "list_date": _json_value(security.list_date),
                "is_active": security.is_active,
                "created_at": _json_value(security.created_at),
                "updated_at": _json_value(security.updated_at),
            }
            for security in securities
        ]
        return success_response(message="证券基础信息查询成功", data={"items": data, "count": len(data)})
    except Exception as exc:
        logger.exception("List securities failed")
        return error_response(message="证券基础信息查询失败", data={"error": str(exc)})


@router.get("/market/kline-daily")
def list_kline_daily(
    symbol: str = Query(..., description="证券代码，例如 510300.SH"),
    limit: int = Query(default=30, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    """查询指定证券的日线行情，按交易日倒序返回。"""

    try:
        statement = (
            select(KlineDaily)
            .where(KlineDaily.symbol == symbol)
            .order_by(desc(KlineDaily.trade_date))
            .limit(limit)
        )
        klines = db.execute(statement).scalars().all()
        data = [
            {
                "id": kline.id,
                "symbol": kline.symbol,
                "trade_date": _json_value(kline.trade_date),
                "open": _json_value(kline.open),
                "high": _json_value(kline.high),
                "low": _json_value(kline.low),
                "close": _json_value(kline.close),
                "volume": _json_value(kline.volume),
                "amount": _json_value(kline.amount),
                "created_at": _json_value(kline.created_at),
            }
            for kline in klines
        ]
        return success_response(message="日线行情查询成功", data={"items": data, "count": len(data)})
    except Exception as exc:
        logger.exception("List kline daily failed: symbol={}", symbol)
        return error_response(message="日线行情查询失败", data={"error": str(exc)})
