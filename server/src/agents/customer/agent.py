#!/usr/bin/env python3
"""客户管理 + 任务调度 Agent（对象化门面）。

与 monitor / business_chat 同范式：节点函数（nodes.py）是 LangGraph 纯函数，
本类封装图构建与元信息，注册到 agent_registry 后由顶层编排图路由调用。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.agents.base import BaseAgent
from src.agents.customer.graph import build_customer_graph
from src.constants import AgentType

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


class CustomerAgent(BaseAgent):
    """客户管理 + 任务调度 Agent：客户状态跟进 / 定时任务 / 自动出报表。"""

    agent_type = AgentType.CUSTOMER
    name = "客户管理 + 任务调度 Agent"
    description = "客户状态跟进、定时任务编排、自动出报表（确定性规则驱动）"

    def build(self) -> "CompiledStateGraph":
        return build_customer_graph()


__all__ = ["CustomerAgent"]
