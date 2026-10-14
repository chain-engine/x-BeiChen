"""API v1 路由包。
在此聚合所有 v1 版本下的业务子路由，统一挂载 /v1 前缀。
未来出 v2 时新建 v2/ 目录，照搬此文件结构即可，router.py 不用动。
"""

from fastapi import APIRouter

from src.api.admin.v1 import (
    auth,
    health,


)
from src.constants import API_VERSION_V1_PREFIX

# v1 聚合路由
v1_router = APIRouter(prefix=API_VERSION_V1_PREFIX)

# 注册健康管理路由
v1_router.include_router(health.router)


# 注册认证管理路由
v1_router.include_router(auth.router)

__all__ = ["v1_router"]
