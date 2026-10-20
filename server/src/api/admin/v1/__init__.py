"""API v1 路由包（北辰 x-BeiChen）。

在此聚合所有 v1 版本下的业务子路由，统一挂载 /v1 前缀。
未来出 v2 时新建 v2/ 目录，照搬本文件结构即可，router.py 不用动。

当前 v1 模块：
    health      健康/版本探针
    auth        认证（预留）
    agent_task  Agent 编排（任务提交/查询/人工接管/事件）
"""

from fastapi import APIRouter

from src.api.admin.v1 import (
    agent_task,
    auth,
    health,
)
from src.constants import API_VERSION_V1_PREFIX

# v1 聚合路由
v1_router = APIRouter(prefix=API_VERSION_V1_PREFIX)

# 健康与版本探针
v1_router.include_router(health.router)

# 认证（预留）
v1_router.include_router(auth.router)

# Agent 编排
v1_router.include_router(agent_task.router)

__all__ = ["v1_router"]
