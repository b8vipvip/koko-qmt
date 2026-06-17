"""数据库表结构初始化脚本。"""

from backend.db.base import Base
from backend.db.session import engine

# 导入所有模型，确保 Base.metadata 能收集完整表结构。
import backend.models  # noqa: F401,E402


def init_db() -> None:
    """创建所有尚不存在的数据库表；只执行 create_all，不删除任何数据。"""

    Base.metadata.create_all(bind=engine)
