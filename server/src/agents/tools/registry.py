#!/usr/bin/env python3
"""工具注册中心（北辰 x-BeiChen）。

工具 = Agent 可调用的外部能力（广告平台 / RAG / 通知）。
权限模型（三级，对齐 ToolPermissionLevel）：
    - read_only      只读：Agent 可直接调用
    - approval_write 审批写：Agent 只能创建审批单（返回 approval_no），审批通过后由执行器执行
    - exec_write     执行写：仅审批执行器可调用，不注册给 Agent

调用约定：Agent 节点通过 tool_registry.invoke(name, permission, **kwargs) 调用，
权限不足时抛 AuthorizationException（应转审批流程而非降级静默）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from src.constants import ToolPermissionLevel
from src.core.exceptions import AuthorizationException
from src.core.logger import logger


@dataclass
class ToolSpec:
    """工具规格。"""

    name: str
    description: str
    func: Callable[..., Any] = field(repr=False)
    permission_level: ToolPermissionLevel = ToolPermissionLevel.READ_ONLY
    enabled: bool = True


class ToolRegistry:
    """工具注册表（应用级单例）。"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            logger.warning(f"工具重复注册，覆盖旧定义：{spec.name}")
        self._tools[spec.name] = spec
        logger.info(f"工具注册成功：{spec.name}（{spec.permission_level}）")

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def invoke(self, name: str, **kwargs: Any) -> Any:
        """调用工具（仅支持只读工具，写工具走审批流程）。

        Args:
            name: 工具名（如 "ads.get_campaign_stats"）
            **kwargs: 工具函数的实际参数

        Returns:
            工具函数执行结果

        Raises:
            ValueError: 工具不存在或已停用
            AuthorizationException: 工具为写工具（APPROVAL_WRITE / EXEC_WRITE），Agent 需走审批流程
        """
        spec = self.get(name)
        if spec is None or not spec.enabled:
            raise ValueError(f"工具不存在或已停用：{name}")
        if spec.permission_level != ToolPermissionLevel.READ_ONLY:
            raise AuthorizationException(
                f"工具 {spec.name} 为写工具（{spec.permission_level}），Agent 需走审批流程"
            )
        logger.info(f"[Tool] invoke {name}")
        return spec.func(**kwargs)

    def list_tools(self) -> list[ToolSpec]:
        return list(self._tools.values())


tool_registry: ToolRegistry = ToolRegistry()

__all__ = ["ToolSpec", "ToolRegistry", "tool_registry"]
