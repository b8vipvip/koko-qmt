"""QMT 连接管理器（Phase 1 mock 版本）。"""

from typing import Any

from loguru import logger

from backend.core.config import settings


class QmtConnectionManager:
    """集中管理 QMT 连接状态，当前阶段仅支持 mock 模式。"""

    def __init__(self) -> None:
        """初始化连接管理器，默认进入 mock 模式。"""

        self.mode = "mock"
        self.connected = False
        self.account_id = settings.qmt_account_id or "MOCK_ACCOUNT"
        self.account_type = settings.qmt_account_type
        self.last_error: str | None = None

    def connect(self) -> dict[str, Any]:
        """建立 mock 连接并返回当前连接状态。"""

        try:
            self.connected = True
            self.last_error = None
            logger.info("QMT mock connected: account_id={}, account_type={}", self.account_id, self.account_type)
            return self.status()
        except Exception as exc:  # pragma: no cover - 防御性异常处理
            self.connected = False
            self.last_error = str(exc)
            logger.exception("QMT mock connect failed")
            raise

    def disconnect(self) -> dict[str, Any]:
        """断开 mock 连接并返回当前连接状态。"""

        try:
            self.connected = False
            self.last_error = None
            logger.info("QMT mock disconnected: account_id={}", self.account_id)
            return self.status()
        except Exception as exc:  # pragma: no cover - 防御性异常处理
            self.last_error = str(exc)
            logger.exception("QMT mock disconnect failed")
            raise

    def status(self) -> dict[str, Any]:
        """查询 mock 连接状态。"""

        try:
            status_data = {
                "mode": self.mode,
                "connected": self.connected,
                "account_id": self.account_id,
                "account_type": self.account_type,
                "last_error": self.last_error,
            }
            logger.info("QMT mock status queried: {}", status_data)
            return status_data
        except Exception as exc:  # pragma: no cover - 防御性异常处理
            self.last_error = str(exc)
            logger.exception("QMT mock status query failed")
            raise

    def query_assets(self) -> dict[str, int]:
        """查询 mock 账户资产示例数据。"""

        try:
            logger.info("QMT mock assets queried: account_id={}", self.account_id)
            return {
                "total_asset": 1000000,
                "cash": 500000,
                "market_value": 500000,
                "available_cash": 500000,
            }
        except Exception as exc:  # pragma: no cover - 防御性异常处理
            self.last_error = str(exc)
            logger.exception("QMT mock assets query failed")
            raise

    def query_positions(self) -> list[dict[str, Any]]:
        """查询 mock 账户持仓示例数据。"""

        try:
            logger.info("QMT mock positions queried: account_id={}", self.account_id)
            return [
                {
                    "symbol": "510300.SH",
                    "name": "沪深300ETF",
                    "volume": 10000,
                    "available_volume": 10000,
                    "market_value": 50000,
                    "cost_price": 5.0,
                    "last_price": 5.0,
                    "profit": 0,
                }
            ]
        except Exception as exc:  # pragma: no cover - 防御性异常处理
            self.last_error = str(exc)
            logger.exception("QMT mock positions query failed")
            raise


qmt_manager = QmtConnectionManager()
