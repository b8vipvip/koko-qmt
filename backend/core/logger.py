"""Loguru 日志初始化模块。"""

import sys
from pathlib import Path

from loguru import logger


LOG_DIR = Path("logs")


def setup_logger() -> None:
    """配置控制台、普通日志和错误日志输出。"""

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stdout, level="INFO", enqueue=True)
    logger.add(LOG_DIR / "info.log", level="INFO", rotation="10 MB", retention="30 days", encoding="utf-8", enqueue=True)
    logger.add(LOG_DIR / "error.log", level="ERROR", rotation="10 MB", retention="30 days", encoding="utf-8", enqueue=True)


setup_logger()
