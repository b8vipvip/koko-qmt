"""数据库连接和会话管理模块。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import settings

# 创建 SQLAlchemy Engine；create_engine 本身不会立即连接 PostgreSQL。
engine = create_engine(settings.get_database_url(), pool_pre_ping=True, future=True)

# 创建会话工厂，供 API 依赖和服务层按需获取数据库会话。
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 数据库依赖：按请求创建并在结束后关闭会话。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
