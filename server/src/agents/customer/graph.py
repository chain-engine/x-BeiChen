#!/usr/bin/env python3
"""客户管理 Agent 子图构建（北辰 x-BeiChen，演示实现）。

子图 = 节点 + 状态（共识：Agent 用一张图实现）。
    START → fetch（拉取客户快照·演示）→ evaluate（跟进判定·演示）
        → compose（编排任务·演示）→ dispatch（执行 + 事件 + 落库·演示）→ END

调度归属：子图不做自循环，周期触发由 APScheduler 外部 job 提交任务（与 monitor 一致）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph

from src.agents.customer.nodes import (
    compose_tasks_node,
    dispatch_node,
    evaluate_status_node,
    fetch_customers_node,
)
from src.agents.customer.state import CustomerState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


def build_customer_graph() -> "CompiledStateGraph":
    """构建客户管理 Agent 子图（已编译，演示节点）。"""
    graph = StateGraph(CustomerState)
    graph.add_node("fetch", fetch_customers_node)
    graph.add_node("evaluate", evaluate_status_node)
    graph.add_node("compose", compose_tasks_node)
    graph.add_node("dispatch", dispatch_node)

    graph.add_edge(START, "fetch")
    graph.add_edge("fetch", "evaluate")
    graph.add_edge("evaluate", "compose")
    graph.add_edge("compose", "dispatch")
    graph.add_edge("dispatch", END)

    return graph.compile()


__all__ = ["build_customer_graph"]
