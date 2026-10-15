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

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from src.constants import AgentType
from src.core.logger import logger

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


@dataclass
class AgentSpec:
    """Agent 规格：注册表的一条记录。"""

    agent_type: AgentType
    name: str
    description: str
    builder: Callable[[], "CompiledStateGraph"] = field(repr=False)
    enabled: bool = True


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
        return self._specs.get(str(agent_type))

    def get_graph(self, agent_type: str | AgentType) -> "CompiledStateGraph":
        """获取编译后的子图（惰性编译 + 缓存）。"""
        key = str(agent_type)
        spec = self._specs.get(key)
        if spec is None:
            raise KeyError(f"Agent 未注册：{key}。可注册类型：{list(self._specs)}")
        if key not in self._graphs:
            self._graphs[key] = spec.builder()
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

    惰性 builder：不 import 业务子图模块，直到首次被路由调用，
    避免编排层初始化时拉入全部 Agent 的依赖。
    """
    from src.agents.business_chat.graph import build_business_chat_graph
    from src.agents.monitor.graph import build_monitor_graph

    agent_registry.register(
        AgentSpec(
            agent_type=AgentType.MONITOR,
            name="数据监控 Agent",
            description="自动拉取广告数据、计算指标、判定异常、告警与建议",
            builder=build_monitor_graph,
        )
    )
    agent_registry.register(
        AgentSpec(
            agent_type=AgentType.BUSINESS_CHAT,
            name="商务对话 Agent",
            description="自动接待客户咨询、RAG 检索政策、生成回复、引导转化、转人工",
            builder=build_business_chat_graph,
        )
    )


# 骨架启动即注册默认 Agent（幂等）
if not agent_registry.has(AgentType.MONITOR):
    register_default_agents()

__all__ = ["AgentSpec", "AgentRegistry", "agent_registry", "register_default_agents"]
