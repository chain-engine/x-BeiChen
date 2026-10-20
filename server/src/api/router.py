#!/usr/bin/env python3
"""
中央路由注册模块（北辰 x-BeiChen）
汇聚管理后台路由，统一挂载 /api 前缀：
    /api/admin/... → 管理后台（北辰 + 审批服务二期嵌入）
    二期扩展：/api/client/...（客户触点）按同样方式新增聚合 router。
"""

from fastapi import APIRouter

from src.api.admin import admin_router
from src.constants import API_PREFIX

# 管理后台业务路由（面向管理员）
global_admin_router = APIRouter(prefix=API_PREFIX)
global_admin_router.include_router(admin_router)

__all__ = ["global_admin_router"]
