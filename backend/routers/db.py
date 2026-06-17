"""数据库状态检查和初始化路由。"""

from sqlalchemy import text
from loguru import logger
from fastapi import APIRouter

from backend.core.response import error_response, success_response
from backend.db.init_db import init_db
from backend.db.session import engine

router = APIRouter(prefix="/api/v1", tags=["db"])


@router.get("/db/status")
def get_db_status() -> dict:
    """检查 PostgreSQL 数据库连接状态。"""

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database status checked successfully")
        return success_response(message="Database connection is healthy", data={"connected": True})
    except Exception as exc:
        logger.exception("Database status check failed")
        return error_response(message="Database connection failed", data={"connected": False, "error": str(exc)})


@router.post("/db/init")
def initialize_db() -> dict:
    """初始化数据库表结构，不执行 drop 或删除数据操作。"""

    try:
        init_db()
        logger.info("Database tables initialized successfully")
        return success_response(message="Database tables initialized successfully", data={"initialized": True})
    except Exception as exc:
        logger.exception("Database table initialization failed")
        return error_response(message="Database initialization failed", data={"initialized": False, "error": str(exc)})
