#!/usr/bin/env python3
"""数据监控 Agent 子图构建（北辰 x-BeiChen）。

子图 = 节点 + 条件边 + 状态（共识：Agent 用一张图实现）。
    START → pull → calc → judge ──normal──▶ END（正常，调度方安排下一轮）
                            └──alert──▶ alert（告警+建议+事件）→ END
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph

from src.agents.monitor.nodes import (
    alert_node,
    calc_metric_node,
    judge_node,
    pull_data_node,
)
from src.agents.monitor.state import MonitorState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


def route_judge(state: MonitorState) -> str:
    """条件边路由：judge 之后走向（normal 正常结束 / alert 进入告警）。"""
    return "alert" if state.get("anomaly") else "normal"


def build_monitor_graph() -> "CompiledStateGraph":
    """构建数据监控 Agent 子图（已编译）。"""
    graph = StateGraph(MonitorState)

    # 节点：拉取投放数据 → 计算指标 → 阈值判定 → 告警
    graph.add_node("pull", pull_data_node)
    graph.add_node("calc", calc_metric_node)
    graph.add_node("judge", judge_node)
    graph.add_node("alert", alert_node)

    # 主干线性边
    graph.add_edge(START, "pull")
    graph.add_edge("pull", "calc")
    graph.add_edge("calc", "judge")

    # 条件边：正常直接结束，异常进入告警节点
    graph.add_conditional_edges("judge", route_judge, {"normal": END, "alert": "alert"})
    graph.add_edge("alert", END)

    return graph.compile()


__all__ = ["build_monitor_graph", "route_judge"]
