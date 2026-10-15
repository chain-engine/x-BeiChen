#!/usr/bin/env python3
"""数据监控 Agent（对象化门面）。

节点函数（nodes.py）仍是 LangGraph 范式的纯函数；本类作为该 Agent 的
对象门面，封装图构建与元信息，使 BaseAgent 抽象真正被继承使用，
同时保持子图内部结构不变。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.agents.base import BaseAgent
from src.agents.monitor.graph import build_monitor_graph
from src.constants import AgentType

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


class MonitorAgent(BaseAgent):
    """数据监控 Agent：拉取投放数据 → 计算指标 → 判定异常 → 告警。"""

    agent_type = AgentType.MONITOR
    name = "数据监控 Agent"
    description = "自动拉取广告数据、计算指标、判定异常、告警与建议"

    def build(self) -> "CompiledStateGraph":
        return build_monitor_graph()
