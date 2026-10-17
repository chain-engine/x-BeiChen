"""API v1 路由包（北辰 x-BeiChen）。

在此聚合所有 v1 版本下的业务子路由，统一挂载 /v1 前缀。
未来出 v2 时新建 v2/ 目录，照搬本文件结构即可，router.py 不用动。

当前 v1 模块：
    health      健康/版本探针
    auth        认证（预留，二期 JWT+RBAC）
    agents      Agent 编排（任务提交/查询/人工接管/事件）
    chat        商务对话（发消息 / 人工接管回复）
    monitoring  数据监控（巡检触发/告警）
    customers   客户管理（CRUD/状态迁移/跟进/报表）
"""

from fastapi import APIRouter

from src.api.admin.v1 import (
    agents,
    auth,
    chat,
    customers,
    health,
    monitoring,
)
from src.constants import API_VERSION_V1_PREFIX

# v1 聚合路由
v1_router = APIRouter(prefix=API_VERSION_V1_PREFIX)

# 健康与版本探针
v1_router.include_router(health.router)

# 认证（预留）
v1_router.include_router(auth.router)

# Agent 编排
v1_router.include_router(agents.router)

# 商务对话
v1_router.include_router(chat.router)

# 数据监控
v1_router.include_router(monitoring.router)

# 客户管理（客户管理 + 任务调度 Agent）
v1_router.include_router(customers.router)

__all__ = ["v1_router"]
