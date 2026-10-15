#!/usr/bin/env python3
"""
中间件模块（北辰 x-BeiChen）
提供 HTTP 请求处理中间件：
    - RequestIDMiddleware：请求 ID 注入（生产级特性，默认预留不注册）
    - RequestLoggingMiddleware：全链路请求记录
    - ExceptionHandlingMiddleware：统一异常处理（404/405/500）
    - AuthMiddleware：认证中间件基础封装（预留，暂不接入）

本期骨架 main.py 默认只注册 ExceptionHandling + RequestLogging；
RequestID / Auth / 限流 / 熔断 等生产级中间件保留实现，接入时在 main.py 取消注释。
"""

import json
import time
import uuid
from collections.abc import Callable
from contextlib import suppress
from typing import Any

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from src.api.response import error_response
from src.constants.enums import HttpHeaders
from src.core.logger import logger
from src.utils.helpers import get_client_ip, mask_sensitive

# 敏感请求头黑名单，日志中始终脱敏
_SENSITIVE_HEADERS: frozenset[str] = frozenset(
    {"authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token", "x-csrftoken"}
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求 ID 中间件。
    为每个请求生成唯一 UUID，注入 request.state.request_id，并在响应头返回 X-Request-ID。
    使用 logger.contextualize() 将 request_id 注入 loguru 上下文，该请求作用域内所有日志自动携带。
    """

    def __init__(self, app: ASGIApp, header_name: str = HttpHeaders.X_REQUEST_ID) -> None:
        super().__init__(app)
        self.header_name: str = header_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id: str | None = request.headers.get(self.header_name)
        if not request_id:
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        with logger.contextualize(request_id=request_id):
            response: Response = await call_next(request)
            response.headers[self.header_name] = request_id
            return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """全链路请求记录：路径、入参、响应耗时、客户端 IP。敏感字段自动脱敏。"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time: float = time.time()
        request_id: str = getattr(request.state, "request_id", "-")
        client_ip: str = get_client_ip(request)
        full_url: str = str(request.url)
        query_params: dict[str, str] = dict(request.query_params)
        safe_headers = mask_sensitive(dict(request.headers), keys=list(_SENSITIVE_HEADERS))
        logger.bind(request_id=request_id).info(
            f"Request started: {request.method} {full_url} from {client_ip} query={query_params} headers={safe_headers}"
        )
        response: Response = await call_next(request)
        elapsed: float = (time.time() - start_time) * 1000
        logger.bind(request_id=request_id).info(
            f"Request completed: {request.method} {full_url} status={response.status_code} duration={elapsed:.2f}ms"
        )
        return response


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """统一异常处理中间件。全局拦截 HTTPException 与未捕获异常，标准化返回。"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except HTTPException as exc:
            request_id: str = getattr(request.state, "request_id", "-")
            logger.bind(request_id=request_id).warning(f"HTTP exception: {exc.status_code} {exc.detail}")
            return error_response(request=request, code=exc.status_code, message=str(exc.detail))
        except Exception as exc:
            request_id = getattr(request.state, "request_id", "-")
            logger.bind(request_id=request_id).exception(f"Unhandled exception: {exc}")
            return error_response(request=request, code=500, message="Internal server error")


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件基础封装（预留）。
    验证 Authorization 头；可配置跳过路径列表。完整 JWT/OAuth 校验接入认证服务后启用。
    """

    def __init__(
        self,
        app: ASGIApp,
        skip_paths: list[str] | None = None,
        token_validator: Callable[[str], bool] | None = None,
    ) -> None:
        super().__init__(app)
        self.skip_paths: list[str] = skip_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/admin/v1/health",
            "/api/admin/v1/version",
        ]
        self.token_validator: Callable[[str], bool] | None = token_validator

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        authorization: str | None = request.headers.get("Authorization")
        if not authorization or not authorization.strip():
            from src.core.exceptions import AuthenticationException

            raise AuthenticationException("Missing Authorization header")
        if self.token_validator is not None:
            token: str = authorization[7:].strip() if authorization.lower().startswith("bearer ") else authorization
            if not self.token_validator(token):
                from src.core.exceptions import AuthenticationException

                raise AuthenticationException("Invalid token")
        return await call_next(request)


__all__ = [
    "RequestIDMiddleware",
    "RequestLoggingMiddleware",
    "ExceptionHandlingMiddleware",
    "AuthMiddleware",
]
