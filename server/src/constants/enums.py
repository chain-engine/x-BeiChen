#!/usr/bin/env python3
"""业务枚举定义。

集中定义项目通用枚举类型，供 schemas / services / repositories 复用。
枚举值对齐数据库列定义，避免业务代码中出现魔法字符串。
按业务类别分组，以横线注释区分。
"""

from enum import Enum

from src.constants.base import IntBaseEnum, StrBaseEnum

# ── 运行环境域 ────────────────────────────────────────


class Environment(StrBaseEnum):
    """运行环境（对齐配置 app_env，可直接与裸字符串比较）。"""

    DEVELOPMENT = "development", "开发环境"
    TESTING = "testing", "测试环境"
    PRODUCTION = "production", "生产环境"


# ── 通用状态域 ────────────────────────────────────────


class CommonStatus(Enum):
    """通用启用/停用状态（对齐 roles、permissions 等表的 status 列）。"""

    ENABLED = "enabled"
    DISABLED = "disabled"


# ── 用户域 ────────────────────────────────────────────


class UserStatus(StrBaseEnum):
    """用户状态（对齐 users.status 列：enabled 启用 / disabled 禁用）。"""

    ENABLED = "enabled", "启用"
    DISABLED = "disabled", "禁用"


class Gender(StrBaseEnum):
    """用户性别（对齐 users.gender 列：male 男 / female 女）。"""

    MALE = "male", "男"
    FEMALE = "female", "女"


# ── 角色权限域 ────────────────────────────────────────


class SystemRoleCode(StrBaseEnum):
    """系统内置角色编码（种子数据中固定存在，不可删除）。"""

    SUPERADMIN = ("superadmin", "超级管理员")
    ADMIN = ("admin", "管理员")
    USER = ("user", "普通用户")



# ── HTTP 域 ───────────────────────────────────────────


class HttpContentType(StrBaseEnum):
    """HTTP Content-Type 媒体类型枚举"""

    APPLICATION_JSON = "application/json", "JSON"
    APPLICATION_OCTET_STREAM = "application/octet-stream", "二进制流"
    APPLICATION_X_WWW_FORM_URLENCODED = "application/x-www-form-urlencoded", "表单数据编码"
    MULTIPART_FORM_DATA = "multipart/form-data", "多部分表单数据"
    TEXT_EVENT_STREAM = "text/event-stream", "事件流（SSE）"


class HttpHeaders(StrBaseEnum):
    """HTTP 请求头"""

    X_REQUEST_ID = "X-Request-ID", "请求ID"
    X_REAL_IP = "X-Real-IP", "真实地址"
    X_FORWARDED_FOR = "X-Forwarded-For", "转发地址"
    AUTHORIZATION = "Authorization", "认证头"
    CONTENT_TYPE = "Content-Type", "内容类型"
    ACCEPT = "Accept", "可接受类型"
    USER_AGENT = "User-Agent", "用户代理"


class HttpStatusCode(IntBaseEnum):
    """HTTP 状态码"""

    OK = 200, "OK"
    CREATED = 201, "Created"
    ACCEPTED = 202, "Accepted"
    NO_CONTENT = 204, "No Content"

    BAD_REQUEST = 400, "Bad Request"
    UNAUTHORIZED = 401, "Unauthorized"
    FORBIDDEN = 403, "Forbidden"
    NOT_FOUND = 404, "Not Found"
    METHOD_NOT_ALLOWED = 405, "Method Not Allowed"
    CONFLICT = 409, "Conflict"
    UNPROCESSABLE_ENTITY = 422, "Unprocessable Entity"
    TOO_MANY_REQUESTS = 429, "Too Many Requests"

    INTERNAL_SERVER_ERROR = 500, "Internal Server Error"
    NOT_IMPLEMENTED = 501, "Not Implemented"
    BAD_GATEWAY = 502, "Bad Gateway"
    SERVICE_UNAVAILABLE = 503, "Service Unavailable"
    GATEWAY_TIMEOUT = 504, "Gateway Timeout"


class ApiResponseCode(IntBaseEnum):
    """API 响应码"""

    SUCCESS = 0, "Success"
    ERROR = -1, "An error occurred"
    VALIDATION_ERROR = 40001, "Validation failed"
    UNAUTHORIZED = 40101, "Unauthorized"
    FORBIDDEN = 40301, "Forbidden"
    NOT_FOUND = 40401, "Resource not found"
    RATE_LIMIT_EXCEEDED = 42901, "Rate limit exceeded"
    SERVER_ERROR = 50001, "Internal server error"
    DATABASE_ERROR = 50002, "Database operation failed"
    EXTERNAL_SERVICE_ERROR = 50003, "External service call failed"
    DOCUMENT_ERROR = 50004, "Document processing failed"
    EMBEDDING_ERROR = 50005, "Embedding generation failed"
    VECTOR_STORE_ERROR = 50006, "Vector store operation failed"
    RETRIEVAL_ERROR = 50007, "Retrieval operation failed"
    GENERATION_ERROR = 50008, "Content generation failed"


class ApiResponseMessage(StrBaseEnum):
    """API 响应消息"""

    SUCCESS = "success", "成功"
    INTERNAL_ERROR = "Internal server error", "内部服务器错误"
    NOT_FOUND = "Resource not found", "资源不存在"
    VALIDATION_ERROR = "Validation error", "参数校验错误"
    AUTHENTICATION_FAILED = "Authentication failed", "认证失败"
    AUTHORIZATION_DENIED = "Permission denied", "权限拒绝"


# ── Agent 编排域 ──────────────────────────────────────────


class AgentType(StrBaseEnum):
    """Agent 类型（业务 Agent 五大分类，mark 同时作为 agent_tasks.task_type 入库值）。"""

    CONTENT = "content", "内容创作 Agent"
    CUSTOMER_SERVICE = "customer_service", "对话（客服）Agent"
    SECURITY = "security", "安全 Agent"
    DATA_ANALYSIS = "data_analysis", "数据分析 Agent"
    DATA_MONITOR = "data_monitor", "数据监控 Agent"


class TaskStatus(StrBaseEnum):
    """Agent 任务状态机（对齐 agent_tasks.status 列）。

    流转：pending → assigned → running → success
                          ↘ failed → retry → running
                          ↘ waiting_human（人工接管中断，resume 后继续）
                                   ↘ abandoned（重试超限，转人工）
    """

    PENDING = "pending", "待派发"
    ASSIGNED = "assigned", "已派发"
    RUNNING = "running", "执行中"
    WAITING_HUMAN = "waiting_human", "等待人工"
    SUCCESS = "success", "成功"
    FAILED = "failed", "失败"
    RETRY = "retry", "待重试"
    ABANDONED = "abandoned", "转人工"


class EventType(StrBaseEnum):
    """Agent 协作事件类型（事件总线消息体 type 字段）。"""

    TASK_FAILED = "task_failed", "任务失败"


class ToolPermissionLevel(StrBaseEnum):
    """工具权限（对齐工具注册中心权限校验）。

    read   只读工具，Agent 可直接调用（查询数据 / 检索知识）
    write  写工具，不注册给 Agent，由人工/外部执行器执行
    """

    READ = "read", "读"
    WRITE = "write", "写"


class AgentRunStatus(StrBaseEnum):
    """Agent 运行状态（可观测面板展示）。"""

    IDLE = "idle", "空闲"
    RUNNING = "running", "运行中"
    WAITING_HUMAN = "waiting_human", "等待人工"
    ERROR = "error", "异常"


class RouteMode(StrBaseEnum):
    """顶层路由模式（对齐 RouteResolver，配置项 agent.route_mode）。

    explicit 仅靠调用方显式 task_type 查表，缺失/非法即失败
    llm      忽略显式值，一律由 LLM 从已注册候选中选择
    hybrid   显式优先命中（零成本），为空/未注册时交 LLM 兜底
    """

    EXPLICIT = "explicit", "显式查表"
    LLM = "llm", "LLM 动态选择"
    HYBRID = "hybrid", "显式优先 LLM 兜底"
