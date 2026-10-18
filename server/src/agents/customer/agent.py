#!/usr/bin/env python3
"""客户管理 Agent（对象化门面，演示实现）。

与 monitor / business_chat 同范式：节点函数（nodes.py）是 LangGraph 纯函数，
本类封装图构建与元信息，注册到 agent_registry 后由顶层编排图路由调用。

当前为演示 Agent：四步链路（fetch → evaluate → compose → dispatch）只产出
演示数据；任务调度保留——周期触发由 APScheduler 外部 job 经
AgentTaskService.submit_task 提交（本 Agent 不做自循环）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.agents.base import BaseAgent
from src.agents.customer.graph import build_customer_graph
from src.constants import AgentType

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


class CustomerAgent(BaseAgent):
    """客户管理 Agent（演示）：客户状态快照 / 跟进判定 / 任务编排 / 执行链路演示。"""

    agent_type = AgentType.CUSTOMER
    name = "客户管理 Agent"
    description = "客户管理 Agent（演示）：fetch → evaluate → compose → dispatch 四步链路演示；任务调度由调度器经 submit_task 触发"

    def build(self) -> "CompiledStateGraph":
        return build_customer_graph()


__all__ = ["CustomerAgent"]
