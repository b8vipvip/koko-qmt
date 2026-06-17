"""统一 API 响应工具。"""

from typing import Any


def success_response(message: str, data: Any | None = None) -> dict[str, Any]:
    """生成项目统一的成功响应结构。"""

    return {
        "success": True,
        "message": message,
        "data": data or {},
    }


def error_response(message: str, data: Any | None = None) -> dict[str, Any]:
    """生成项目统一的失败响应结构。"""

    return {
        "success": False,
        "message": message,
        "data": data or {},
    }
