#!/usr/bin/env python3
"""通用全局常量。

集中定义应用信息、请求上下文键、
用户字段约束等全局常量。禁止在业务代码中硬编码这些值。
按业务类别分组，以横线注释区分。
"""

# ── 配置文件 ──────────────────────────────────────────
DEFAULT_CONFIG_DIR: str = "."
DEFAULT_CONFIG_FILE: str = "config.yaml"


# ── 应用信息 ──────────────────────────────────────────
APP_ID: str = "x-BeiChen"
APP_NAME: str = "北辰（BeiChen）"
APP_DESCRIPTION: str = "XXXXX"
APP_VERSION: str = "0.1.0"

# ── API 路由 ──────────────────────────────────────────
# 基础前缀；具体版本号（/v1）由各路由组在自己的 router 上声明，
# 例如：管理系统 /api/admin/v1
API_PREFIX: str = "/api"
ADMIN_PREFIX: str = "/admin"
API_VERSION_V1_PREFIX: str = "/v1"


# ── 账号与令牌 ────────────────────────────────────────

# 用户名长度约束
USERNAME_MIN_LENGTH: int = 3
USERNAME_MAX_LENGTH: int = 50

# 登录态 / 访问令牌有效期（秒）＝ 7 天；与配置 auth.access_token_expire_minutes 对齐
TOKEN_TTL_SECONDS: int = 60 * 60 * 24 * 7
