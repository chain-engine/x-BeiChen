#!/usr/bin/env python3
"""
中央路由注册模块
"""

from fastapi import APIRouter

from src.api.admin import admin_router



# 管理后台业务路由（面向管理员，会话 JWT + Redis 登录态）
global_admin_router = APIRouter(prefix=API_PREFIX)
global_admin_router.include_router(admin_router)
