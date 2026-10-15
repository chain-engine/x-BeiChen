#!/usr/bin/env python3
"""
应用配置管理模块（北辰 x-BeiChen）
支持从环境变量和 YAML 配置文件读取配置，使用 dataclass 描述各配置段。
配置优先级：环境变量 > 环境特定配置(config.{env}.yaml) > 默认配置(config.yaml) > 代码默认值。

Usage:
    from src.core.config import settings
    port = settings.server.port
    model = settings.ai.llm.model
"""

import os
from dataclasses import dataclass, field
from typing import Any, Final
from urllib.parse import quote_plus

import yaml

from src.constants import DEFAULT_CONFIG_DIR, Environment
from src.core.logger import logger
from src.utils.convert import to_bool, to_float, to_int
from src.utils.helpers import find_project_root

# 明确禁止使用的弱密钥
_FORBIDDEN_SECRET_KEYS: frozenset[str] = frozenset(
    {"change-me-in-production", "change-me", "secret", "default", "changeme", ""}
)


# ============================================================
# Dataclass 配置段
# ============================================================

@dataclass
class ServerConfig:
    """服务器配置。"""

    host: str = "0.0.0.0"
    port: int = 6666
    debug: bool = True
    workers: int = 1


@dataclass
class LoggingConfig:
    """日志配置。"""

    level: str = "INFO"
    format: str = "console"  # "json" | "console"
    file_path: str = "logs/x-BeiChen-{time:YYYYMMDDHH}.log"
    rotation: str = "1 day"
    retention: str = "7 days"
    compression: str = "zip"
    console_output: bool = True


@dataclass
class CORSConfig:
    """跨域配置。"""

    enabled: bool = True
    origins: list[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: list[str] = field(default_factory=lambda: ["*"])
    allow_headers: list[str] = field(default_factory=lambda: ["*"])


@dataclass
class DatabaseConfig:
    """数据库配置（本期骨架可整体不启用）。"""

    enabled: bool = False  # 骨架阶段默认关闭，业务接入时开启
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "beichen"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    @property
    def url(self) -> str:
        """根据结构化数据库配置生成 SQLAlchemy 连接串。"""
        if not self.password:
            return ""
        return (
            f"mysql+pymysql://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{quote_plus(self.database)}"
        )


@dataclass
class RedisConfig:
    """Redis 配置（缓存 / 事件总线 / Agent 检查点）。"""

    enabled: bool = False  # 骨架阶段默认关闭
    host: str = "localhost"
    port: int = 6379
    user: str = "default"
    password: str = ""
    db: int = 0
    pool_size: int = 10
    max_connections: int = 50
    decode_responses: bool = True
    socket_timeout: int = 5

    @property
    def url(self) -> str:
        """根据结构化 Redis 配置生成连接串。"""
        credentials = f"{quote_plus(self.user)}:{quote_plus(self.password)}@" if self.password else ""
        return f"redis://{credentials}{self.host}:{self.port}/{self.db}"


@dataclass
class AILLMConfig:
    """大模型配置（LangChain ChatOpenAI 兼容接口）。
    provider: "openai_compat" —— OpenAI 兼容协议，可对接豆包方舟 / DeepSeek / 本地 vLLM 等。
    """

    provider: str = "openai_compat"
    base_url: str = "https://api.xiaomimimo.com/v1"
    api_key: str = ""  # 敏感信息，仅通过环境变量 / .env 注入
    model: str = "mimo-v2.6-pro"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_seconds: int = 60


@dataclass
class AIConfig:
    """AI 整体配置（本期骨架：LLM 预留，节点内业务为 mock）。"""

    enabled: bool = True
    llm: AILLMConfig = field(default_factory=AILLMConfig)


@dataclass
class AgentConfig:
    """Agent 编排配置（调度中枢 / 子图 / 任务状态机）。"""

    enabled: bool = True
    # checkpointer 存储："memory"（内存，开发）| "redis"（生产，需 RedisConfig.enabled）
    checkpoint: str = "memory"
    task_max_retries: int = 3  # 失败重试上限（指数退避）
    task_timeout_seconds: int = 300
    event_bus_stream: str = "beichen:agent:events"  # Redis Stream 事件总线
    agent_specs_module: str = "src.agents"  # Agent 注册表扫描模块（预留）


@dataclass
class ApprovalConfig:
    """审批闸门配置（广告审批系统对接，预留）。
    资金类写操作一律经广告审批后由执行器执行，Agent 不直接调用。
    """

    enabled: bool = True
    base_url: str = "http://approval-service:8080"  # 广告审批服务地址
    api_prefix: str = "/api/v1"
    timeout_seconds: int = 10
    service_token: str = ""  # 服务间鉴权令牌（预留）


# ============================================================
# 环境变量 → YAML 配置段 映射
# ============================================================

_ENV_SECTION_MAP: dict[str, tuple[str, list[str]]] = {
    "server": ("SERVER_", ["host", "port", "debug", "workers"]),
    "logging": ("LOGGING_", ["level", "format", "file_path", "rotation", "retention", "compression", "console_output"]),
    "cors": ("CORS_", ["enabled", "origins", "allow_credentials", "allow_methods", "allow_headers"]),
    "database": ("DATABASE_", ["enabled", "host", "port", "user", "password", "database", "pool_size", "echo"]),
    "redis": ("REDIS_", ["enabled", "host", "port", "user", "password", "db", "decode_responses", "socket_timeout"]),
    "ai": ("AI_", ["enabled"]),
    "agent": (
        "AGENT_",
        ["enabled", "checkpoint", "task_max_retries", "task_timeout_seconds", "event_bus_stream"],
    ),
    "approval": ("APPROVAL_", ["enabled", "base_url", "api_prefix", "timeout_seconds", "service_token"]),
}


# ============================================================
# 核心配置类
# ============================================================

class Settings:
    """应用全局配置类。
    配置加载优先级（从高到低）：
        1. 环境变量
        2. 环境特定 YAML 配置（config.{env}.yaml）
        3. 默认 YAML 配置（config.yaml）
        4. 代码中的默认值
    """

    def __init__(self) -> None:
        self._config: dict[str, Any] = self._load_config()
        self._parse_config()

    # ----------------------------------------------------------
    # 配置加载
    # ----------------------------------------------------------

    def _get_default_config(self) -> dict[str, Any]:
        """返回所有配置段的代码默认值。"""
        return {
            "app_env": Environment.DEVELOPMENT,
            "server": {"host": "0.0.0.0", "port": 6666, "debug": True, "workers": 1},
            "logging": {
                "level": "INFO",
                "format": "console",
                "file_path": "logs/x-BeiChen-{time:YYYYMMDDHH}.log",
                "rotation": "1 day",
                "retention": "7 days",
                "compression": "zip",
                "console_output": True,
            },
            "cors": {"enabled": True, "origins": ["*"], "allow_credentials": True, "allow_methods": ["*"], "allow_headers": ["*"]},
            "database": {"enabled": False, "host": "localhost", "port": 3306, "user": "root", "password": "", "database": "beichen", "pool_size": 5, "max_overflow": 10, "pool_timeout": 30, "pool_recycle": 3600, "echo": False},
            "redis": {"enabled": False, "host": "localhost", "port": 6379, "user": "default", "password": "", "db": 0, "pool_size": 10, "max_connections": 50, "decode_responses": True, "socket_timeout": 5},
            "ai": {
                "enabled": True,
                "llm": {
                    "provider": "openai_compat",
                    "base_url": "https://api.xiaomimimo.com/v1",
                    "api_key": "",
                    "model": "mimo-v2.6-pro",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "timeout_seconds": 60,
                },
            },
            "agent": {
                "enabled": True,
                "checkpoint": "memory",
                "task_max_retries": 3,
                "task_timeout_seconds": 300,
                "event_bus_stream": "beichen:agent:events",
                "agent_specs_module": "src.agents",
            },
            "approval": {
                "enabled": True,
                "base_url": "http://approval-service:8080",
                "api_prefix": "/api/v1",
                "timeout_seconds": 10,
                "service_token": "",
            },
        }

    def _merge_config(self, base: dict[str, Any], override: dict[str, Any]) -> None:
        """递归合并配置字典，override 覆盖 base 同名键。"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _load_config(self) -> dict[str, Any]:
        """加载配置，优先级：环境变量 > YAML > 默认值。"""
        config = self._get_default_config()
        self._load_from_yaml(config)
        self._load_from_env(config)
        return config

    def _load_from_yaml(self, config: dict[str, Any]) -> None:
        """从 YAML 文件加载配置（config.yaml → config.{env}.yaml）。"""
        project_root = find_project_root()
        config_dir = project_root / DEFAULT_CONFIG_DIR
        env_dot_file = project_root / ".env"
        if env_dot_file.exists():
            try:
                from dotenv import load_dotenv

                load_dotenv(env_dot_file, override=False)
            except Exception as e:
                logger.warning(f"Cannot load .env file {env_dot_file}: {e}")
        default_file = config_dir / "config.yaml"
        if default_file.exists():
            try:
                with open(default_file, encoding="utf-8") as f:
                    default_cfg = yaml.safe_load(f) or {}
                if isinstance(default_cfg, dict):
                    self._merge_config(config, default_cfg)
            except Exception as e:
                logger.warning(f"Cannot load config file {default_file}: {e}")
        app_env = os.environ.get("APP_ENV", config.get("app_env", Environment.DEVELOPMENT))
        env_file = config_dir / f"config.{app_env}.yaml"
        if env_file.exists():
            try:
                with open(env_file, encoding="utf-8") as f:
                    env_cfg = yaml.safe_load(f) or {}
                if isinstance(env_cfg, dict):
                    self._merge_config(config, env_cfg)
            except Exception as e:
                logger.warning(f"Cannot load config file {env_file}: {e}")

    def _load_from_env(self, config: dict[str, Any]) -> None:
        """从环境变量加载配置，覆盖 YAML 和默认值。"""
        if value := os.environ.get("APP_ENV"):
            config["app_env"] = value
        for section_name, (prefix, keys) in _ENV_SECTION_MAP.items():
            if section_name not in config:
                continue
            section = config[section_name]
            for key in keys:
                env_key = f"{prefix}{key.upper()}"
                value = os.environ.get(env_key)
                if value is None:
                    continue
                default_val = section.get(key)
                if isinstance(default_val, bool):
                    section[key] = to_bool(value)
                elif isinstance(default_val, int):
                    section[key] = to_int(value)
                elif isinstance(default_val, float):
                    section[key] = to_float(value)
                elif isinstance(default_val, list):
                    section[key] = [v.strip() for v in value.split(",")]
                else:
                    section[key] = value
        # AI 嵌套配置（AI_LLM_*）
        ai = config.setdefault("ai", {})
        ai_llm = ai.setdefault("llm", {})
        for env_key, key in {
            "AI_LLM_PROVIDER": "provider",
            "AI_LLM_BASE_URL": "base_url",
            "AI_LLM_API_KEY": "api_key",
            "AI_LLM_MODEL": "model",
        }.items():
            if value := os.environ.get(env_key):
                ai_llm[key] = value
        if value := os.environ.get("AI_LLM_TEMPERATURE"):
            ai_llm["temperature"] = to_float(value)
        if value := os.environ.get("AI_LLM_MAX_TOKENS"):
            ai_llm["max_tokens"] = to_int(value)

    # ----------------------------------------------------------
    # 解析到 dataclass
    # ----------------------------------------------------------

    def _parse_config(self) -> None:
        self.app_env: str = self._config.get("app_env", Environment.DEVELOPMENT)
        self.server = ServerConfig(**self._config.get("server", {}))
        self.logging = LoggingConfig(**self._config.get("logging", {}))
        self.cors = CORSConfig(**self._config.get("cors", {}))
        self.database = DatabaseConfig(**self._config.get("database", {}))
        self.redis = RedisConfig(**self._config.get("redis", {}))
        ai_raw = self._config.get("ai", {})
        self.ai = AIConfig(enabled=ai_raw.get("enabled", True), llm=AILLMConfig(**ai_raw.get("llm", {})))
        self.agent = AgentConfig(**self._config.get("agent", {}))
        self.approval = ApprovalConfig(**self._config.get("approval", {}))

    # ----------------------------------------------------------
    # 环境判断
    # ----------------------------------------------------------

    @property
    def is_development(self) -> bool:
        return self.app_env == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.app_env == Environment.TESTING

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    # ----------------------------------------------------------
    # 配置校验
    # ----------------------------------------------------------

    def validate(self) -> None:
        """验证配置合法性，配置错误直接阻断启动。"""
        if len(self.ai.llm.api_key) and len(self.ai.llm.api_key) < 8:
            raise ValueError("AI_LLM_API_KEY 长度异常（至少 8 字符，未配置可留空走 mock）")
        if self.is_production:
            if self.server.debug:
                raise ValueError("DEBUG mode must be disabled in production")
            if self.database.enabled and not self.database.url:
                raise ValueError("DATABASE_URL 在生产环境必须配置")
            if self.redis.enabled and not self.redis.url:
                raise ValueError("REDIS_URL 在生产环境必须配置")

    # ----------------------------------------------------------
    # 热重载
    # ----------------------------------------------------------

    def reload(self) -> None:
        """重新加载全部配置并重新校验。"""
        self._config = self._load_config()
        self._parse_config()
        self.validate()


# ============================================================
# 全局单例
# ============================================================
settings: Final[Settings] = Settings()
settings.validate()
