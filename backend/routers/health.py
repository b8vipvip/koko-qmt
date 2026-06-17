"""健康检查路由。"""

from fastapi import APIRouter

from backend.core.config import settings
from backend.core.response import success_response

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """返回后端服务运行状态。"""

    return success_response(
        message="koko-qmt backend is running",
        data={
            "app": "koko-qmt",
            "mode": settings.app_env,
        },
    )
