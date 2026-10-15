"""常量与枚举包（北辰 x-BeiChen）。

子模块：
    base      枚举基类族（BaseEnum / StrBaseEnum / IntBaseEnum）
    constants 全局常量（应用信息 / API 路由 / 账号约束）
    enums     业务枚举（环境 / HTTP / Agent 编排域）
"""

from src.constants.base import BaseEnum, FloatBaseEnum, IntBaseEnum, StrBaseEnum
from src.constants.constants import (
    ADMIN_PREFIX,
    API_PREFIX,
    API_VERSION_V1_PREFIX,
    APP_DESCRIPTION,
    APP_ID,
    APP_NAME,
    APP_VERSION,
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_FILE,
    TOKEN_TTL_SECONDS,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)
from src.constants.enums import (
    AgentRunStatus,
    AgentType,
    ApiResponseCode,
    ApiResponseMessage,
    CommonStatus,
    Environment,
    EventType,
    Gender,
    HttpContentType,
    HttpHeaders,
    HttpStatusCode,
    SystemRoleCode,
    TaskStatus,
    ToolPermissionLevel,
    UserStatus,
)

__all__ = [
    # 基类
    "BaseEnum",
    "StrBaseEnum",
    "IntBaseEnum",
    "FloatBaseEnum",
    # 常量
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_CONFIG_FILE",
    "APP_ID",
    "APP_NAME",
    "APP_DESCRIPTION",
    "APP_VERSION",
    "API_PREFIX",
    "ADMIN_PREFIX",
    "API_VERSION_V1_PREFIX",
    "USERNAME_MIN_LENGTH",
    "USERNAME_MAX_LENGTH",
    "TOKEN_TTL_SECONDS",
    # 枚举
    "Environment",
    "CommonStatus",
    "UserStatus",
    "Gender",
    "SystemRoleCode",
    "HttpContentType",
    "HttpHeaders",
    "HttpStatusCode",
    "ApiResponseCode",
    "ApiResponseMessage",
    "AgentType",
    "TaskStatus",
    "EventType",
    "ToolPermissionLevel",
    "AgentRunStatus",
]
