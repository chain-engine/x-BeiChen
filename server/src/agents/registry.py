#!/usr/bin/env python3
"""Agent 注册表（映射表路由的标准实现，北辰 x-BeiChen）。

职责：
    1. 注册：AgentType → AgentSpec（含子图惰性构建器）
    2. 路由：task_type → AgentSpec（"派给谁"由映射表决定）
    3. 编译缓存：子图只编译一次，重复复用

与 LangGraph 的分工（共识）：
    - 注册表回答"派给谁"（task_type → Agent 的静态映射）
    - LangGraph 回答"怎么干"（子图内部步骤 / 生命周期 / 中断恢复）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.agents.base import BaseAgent
from src.constants import AgentType
from src.core.logger import logger

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


@dataclass
class AgentSpec:
    """Agent 规格：注册表的一条记录，持有 Agent 对象门面。"""

    agent: BaseAgent
    enabled: bool = True

    @property
    def agent_type(self) -> AgentType:
        return self.agent.agent_type

    @property
    def name(self) -> str:
        return self.agent.name

    @property
    def description(self) -> str:
        return self.agent.description


class AgentRegistry:
    """Agent 注册表（应用级单例，持编译缓存）。"""

    def __init__(self) -> None:
        self._specs: dict[str, AgentSpec] = {}
        self._graphs: dict[str, "CompiledStateGraph"] = {}

    # ----------------------------------------------------------
    # 注册
    # ----------------------------------------------------------

    def register(self, spec: AgentSpec) -> None:
        key = str(spec.agent_type)
        if key in self._specs:
            logger.warning(f"Agent 重复注册，覆盖旧定义：{key}")
        self._specs[key] = spec
        logger.info(f"Agent 注册成功：{key}（{spec.name}）")

    # ----------------------------------------------------------
    # 查询 / 路由
    # ----------------------------------------------------------

    def get_spec(self, agent_type: str | AgentType) -> AgentSpec | None:
        """根据 AgentType 获取 AgentSpec。"""
        return self._specs.get(str(agent_type))

    def get_graph(self, agent_type: str | AgentType) -> "CompiledStateGraph":
        """获取编译后的子图（惰性编译 + 缓存）。"""
        key = str(agent_type)
        spec = self._specs.get(key)
        if spec is None:
            raise KeyError(f"Agent 未注册：{key}。可注册类型：{list(self._specs)}")
        if key not in self._graphs:
            self._graphs[key] = spec.agent.build()
            logger.info(f"Agent 子图编译完成：{key}")
        return self._graphs[key]

    def route(self, task_type: str | AgentType) -> AgentSpec:
        """映射表路由：task_type → AgentSpec。"""
        spec = self.get_spec(task_type)
        if spec is None:
            raise KeyError(f"无法路由任务：{task_type}，未注册对应 Agent")
        if not spec.enabled:
            raise ValueError(f"Agent 已停用：{task_type}")
        return spec

    def list_specs(self) -> list[AgentSpec]:
        return list(self._specs.values())

    def has(self, agent_type: str | AgentType) -> bool:
        return str(agent_type) in self._specs


# ============================================================
# 全局单例：北辰当前注册的 Agent（二期占位枚举保留，未注册即不可路由）
# ============================================================

agent_registry: AgentRegistry = AgentRegistry()


def register_default_agents() -> None:
    """注册当前骨架已实现的 Agent（数据监控 / 商务对话）。

    注册 Agent 对象门面实例；子图在首次被路由时才通过 agent.build() 惰性编译，
    避免编排层初始化时拉入全部业务依赖。
    """
    from src.agents.business_chat.agent import BusinessChatAgent
    from src.agents.monitor.agent import MonitorAgent

    agent_registry.register(AgentSpec(agent=MonitorAgent()))
    agent_registry.register(AgentSpec(agent=BusinessChatAgent()))


# 骨架启动即注册默认 Agent（幂等）
if not agent_registry.has(AgentType.MONITOR):
    register_default_agents()

__all__ = ["AgentSpec", "AgentRegistry", "agent_registry", "register_default_agents"]
