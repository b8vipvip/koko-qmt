"""数据中心 mock 同步引擎。"""

from __future__ import annotations

import threading
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.models.market import KlineDaily, SecurityInfo


class DataSyncEngine:
    """维护数据同步任务状态，并执行 mock 行情数据写入。"""

    def __init__(self) -> None:
        """初始化同步状态。"""

        self.running = False
        self.progress = 0
        self.status = "idle"
        self.message = "等待同步"
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.last_error: str | None = None
        self._lock = threading.Lock()

    def mark_started(self, message: str = "mock 数据同步任务已提交") -> bool:
        """在 API 请求线程中预先标记任务开始，避免重复提交后台任务。"""

        with self._lock:
            if self.running:
                return False
            self.running = True
            self.progress = 0
            self.status = "running"
            self.message = message
            self.started_at = datetime.now(timezone.utc)
            self.finished_at = None
            self.last_error = None
            return True

    def _update_status(
        self,
        *,
        progress: int | None = None,
        status: str | None = None,
        message: str | None = None,
    ) -> None:
        """线程安全地更新同步进度状态。"""

        with self._lock:
            if progress is not None:
                self.progress = progress
            if status is not None:
                self.status = status
            if message is not None:
                self.message = message

    def _finish_success(self) -> None:
        """线程安全地标记同步成功。"""

        with self._lock:
            self.running = False
            self.progress = 100
            self.status = "success"
            self.message = "mock 数据同步成功"
            self.finished_at = datetime.now(timezone.utc)

    def _finish_failed(self, exc: Exception) -> None:
        """线程安全地标记同步失败并记录最近错误。"""

        with self._lock:
            self.running = False
            self.status = "failed"
            self.message = "mock 数据同步失败"
            self.finished_at = datetime.now(timezone.utc)
            self.last_error = str(exc)

    def get_status(self) -> dict[str, Any]:
        """返回当前同步任务状态，datetime 转为 ISO 字符串方便 JSON 序列化。"""

        with self._lock:
            return {
                "running": self.running,
                "progress": self.progress,
                "status": self.status,
                "message": self.message,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "finished_at": self.finished_at.isoformat() if self.finished_at else None,
                "last_error": self.last_error,
            }

    def start_mock_sync(self, db: Session) -> None:
        """执行 mock 数据同步，写入证券基础信息和最近 10 个交易日的日线数据。"""

        try:
            with self._lock:
                self.running = True
                self.progress = 10
                self.status = "running"
                self.message = "开始同步 mock 证券基础信息"
                self.started_at = self.started_at or datetime.now(timezone.utc)
                self.finished_at = None
                self.last_error = None

            logger.info("Mock data sync started")
            securities = self._build_mock_securities()
            self._upsert_securities(db, securities)
            db.commit()
            self._update_status(progress=30, message="mock 证券基础信息同步完成")
            logger.info("Mock security_info sync finished, count={}", len(securities))
            time.sleep(0.1)

            self._update_status(progress=60, message="开始同步 mock 日线行情")
            klines = self._build_mock_klines(securities)
            self._upsert_klines(db, klines)
            db.commit()
            self._update_status(progress=90, message="mock 日线行情同步完成")
            logger.info("Mock kline_daily sync finished, count={}", len(klines))
            time.sleep(0.1)

            self._finish_success()
            logger.info("Mock data sync succeeded")
        except Exception as exc:
            db.rollback()
            self._finish_failed(exc)
            logger.exception("Mock data sync failed")

    def _build_mock_securities(self) -> list[dict[str, Any]]:
        """构造可重复写入的 mock 证券基础信息。"""

        return [
            {
                "symbol": "510300.SH",
                "name": "沪深300ETF",
                "exchange": "SH",
                "asset_type": "ETF",
                "list_date": date(2012, 5, 28),
                "is_active": True,
            },
            {
                "symbol": "510500.SH",
                "name": "中证500ETF",
                "exchange": "SH",
                "asset_type": "ETF",
                "list_date": date(2013, 3, 15),
                "is_active": True,
            },
            {
                "symbol": "159915.SZ",
                "name": "创业板ETF",
                "exchange": "SZ",
                "asset_type": "ETF",
                "list_date": date(2011, 9, 20),
                "is_active": True,
            },
            {
                "symbol": "588000.SH",
                "name": "科创50ETF",
                "exchange": "SH",
                "asset_type": "ETF",
                "list_date": date(2020, 9, 28),
                "is_active": True,
            },
            {
                "symbol": "000001.SZ",
                "name": "平安银行",
                "exchange": "SZ",
                "asset_type": "STOCK",
                "list_date": date(1991, 4, 3),
                "is_active": True,
            },
        ]

    def _build_mock_klines(self, securities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """为每个 mock 证券构造最近 10 个自然日工作日风格的日线数据。"""

        trade_dates: list[date] = []
        current_day = date.today()
        while len(trade_dates) < 10:
            if current_day.weekday() < 5:
                trade_dates.append(current_day)
            current_day -= timedelta(days=1)
        trade_dates.reverse()

        rows: list[dict[str, Any]] = []
        for security_index, security in enumerate(securities):
            base_price = Decimal("1.0000") + Decimal(security_index) * Decimal("2.0000")
            for day_index, trade_day in enumerate(trade_dates):
                close_price = base_price + Decimal(day_index) * Decimal("0.0300")
                open_price = close_price - Decimal("0.0100")
                high_price = close_price + Decimal("0.0200")
                low_price = close_price - Decimal("0.0300")
                volume = Decimal(1_000_000 + security_index * 100_000 + day_index * 10_000)
                rows.append(
                    {
                        "symbol": security["symbol"],
                        "trade_date": trade_day,
                        "open": open_price,
                        "high": high_price,
                        "low": low_price,
                        "close": close_price,
                        "volume": volume,
                        "amount": volume * close_price,
                    }
                )
        return rows

    def _upsert_securities(self, db: Session, rows: list[dict[str, Any]]) -> None:
        """按 symbol 唯一约束 upsert 证券基础信息，不删除已有数据。"""

        statement = insert(SecurityInfo).values(rows)
        update_columns = {
            column: getattr(statement.excluded, column)
            for column in ["name", "exchange", "asset_type", "list_date", "is_active"]
        }
        db.execute(statement.on_conflict_do_update(index_elements=["symbol"], set_=update_columns))

    def _upsert_klines(self, db: Session, rows: list[dict[str, Any]]) -> None:
        """按 symbol + trade_date 唯一约束 upsert 日线行情，不删除已有数据。"""

        statement = insert(KlineDaily).values(rows)
        update_columns = {
            column: getattr(statement.excluded, column)
            for column in ["open", "high", "low", "close", "volume", "amount"]
        }
        db.execute(statement.on_conflict_do_update(index_elements=["symbol", "trade_date"], set_=update_columns))


data_sync_engine = DataSyncEngine()
