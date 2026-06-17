"""QMT mock 连接和账户查询路由。"""

from fastapi import APIRouter
from loguru import logger

from backend.core.response import error_response, success_response
from backend.services.qmt.connection_manager import qmt_manager

router = APIRouter(prefix="/api/v1", tags=["qmt"])


@router.get("/qmt/status")
def get_qmt_status() -> dict:
    """获取 QMT mock 连接状态。"""

    try:
        return success_response(message="QMT connection status queried", data=qmt_manager.status())
    except Exception as exc:
        logger.exception("Failed to query QMT status")
        return error_response(message=f"Failed to query QMT status: {exc}")


@router.post("/qmt/connect")
def connect_qmt() -> dict:
    """建立 QMT mock 连接。"""

    try:
        return success_response(message="QMT connected successfully", data=qmt_manager.connect())
    except Exception as exc:
        logger.exception("Failed to connect QMT")
        return error_response(message=f"Failed to connect QMT: {exc}")


@router.post("/qmt/disconnect")
def disconnect_qmt() -> dict:
    """断开 QMT mock 连接。"""

    try:
        return success_response(message="QMT disconnected successfully", data=qmt_manager.disconnect())
    except Exception as exc:
        logger.exception("Failed to disconnect QMT")
        return error_response(message=f"Failed to disconnect QMT: {exc}")


@router.get("/account/assets")
def get_account_assets() -> dict:
    """获取 mock 账户资产。"""

    try:
        return success_response(message="Account assets queried", data=qmt_manager.query_assets())
    except Exception as exc:
        logger.exception("Failed to query account assets")
        return error_response(message=f"Failed to query account assets: {exc}")


@router.get("/account/positions")
def get_account_positions() -> dict:
    """获取 mock 账户持仓。"""

    try:
        return success_response(message="Account positions queried", data=qmt_manager.query_positions())
    except Exception as exc:
        logger.exception("Failed to query account positions")
        return error_response(message=f"Failed to query account positions: {exc}")
