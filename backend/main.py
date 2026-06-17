"""koko-qmt FastAPI 后端入口。"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from backend.core.config import settings
from backend.core.logger import setup_logger
from backend.core.response import error_response
from backend.routers.health import router as health_router
from backend.routers.qmt import router as qmt_router
from backend.routers.db import router as db_router
from backend.routers.data import router as data_router

setup_logger()

app = FastAPI(title="koko-qmt backend", version="0.1.0")
app.include_router(health_router)
app.include_router(qmt_router)
app.include_router(db_router)
app.include_router(data_router)


@app.on_event("startup")
def on_startup() -> None:
    """应用启动时记录当前运行模式。"""

    logger.info(
        "koko-qmt backend started: env={}, host={}, port={}, trade_mode={}, enable_real_trade={}",
        settings.app_env,
        settings.app_host,
        settings.app_port,
        settings.trade_mode,
        settings.enable_real_trade,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """捕获未处理异常并写入错误日志。"""

    logger.exception("Unhandled error while processing {} {}", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_response(message="internal server error"),
    )
