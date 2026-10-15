#!/usr/bin/env python3
"""认证接口（北辰 x-BeiChen，预留）。

鉴权为生产级特性，本期骨架不接入：
    - POST /auth/login —— 预留：JWT 签发（二期对接 RBAC 用户体系）
    - POST /auth/refresh —— 预留：令牌刷新
当前返回 501 Not Implemented，提示接入方式。
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.api.response import error_response
from src.constants import HttpStatusCode

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", status_code=501)
async def login(request: Request) -> JSONResponse:
    """登录（预留接口）。

    TODO(二期): JWT + Redis 登录态签发，对齐 RBAC 权限体系；
    本期骨架仅返回 501，提示接入。
    """
    return error_response(
        request=request,
        code=HttpStatusCode.NOT_IMPLEMENTED.mark,
        message="认证接口预留：二期接入 JWT + RBAC 后启用（见 src/api/admin/permission_decorator.py）",
    )


@router.post("/refresh", status_code=501)
async def refresh(request: Request) -> JSONResponse:
    """刷新令牌（预留接口）。"""
    return error_response(
        request=request,
        code=HttpStatusCode.NOT_IMPLEMENTED.mark,
        message="令牌刷新接口预留：二期接入",
    )
