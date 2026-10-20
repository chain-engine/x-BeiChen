#!/usr/bin/env python3
"""权限控制装饰器（北辰 x-BeiChen，预留）。

RBAC 鉴权为生产级特性，骨架阶段不接入。
提供装饰器占位与说明，接入时按统一风格启用：
    - require_permission(role)：接口级角色校验
    - 与 AuthMiddleware / 用户体系（RBAC 权限表）联动
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable


def require_permission(*roles: str) -> Callable[..., Any]:
    """接口级角色权限校验（预留装饰器）。

    Usage:
        @router.post("/tasks")
        @require_permission("admin", "operator")
        async def submit_task(...): ...

    TODO: 接入 JWT 解析 + RBAC 权限表校验；
    当前为占位实现，不做任何拦截（保证骨架接口可用）。
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # TODO: 校验 request.state.user 的角色是否在 roles 内，
            # 不满足抛 AuthorizationException。
            return await func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["require_permission"]
