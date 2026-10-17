#!/usr/bin/env python3
"""顶层调度中枢编排图（北辰 x-BeiChen，Hybrid 分层混合的标准形态）。

图结构（节点 + 条件边 + 状态）：
    START ──▶ route（映射表路由）
                   │
                   ├─ conditional（按 target_agent 动态路由）
                   ▼
              monitor 子图节点 ──┐
           business_chat 子图节点 ─┤──▶ aggregate（聚合）──▶ END
             （二期继续挂新子图）   ┘

关键设计（LangGraph 官方标准）：
    - 编译后的业务子图直接 add_node 注册为顶层图节点
      （框架统一处理嵌套 checkpoint / interrupt / resume，无需手动 invoke）
    - 动态路由：route 节点把 target_agent 写入状态，条件边按它分发到对应子图
    - 子图私有字段不声明在 OrchestratorState，输出自动忽略，不污染顶层

职责划分（共识）：
    - 编排图：管"怎么干" —— 派活链路、子图生命周期、中断恢复、结果聚合
    - 注册表：管"派给谁" —— task_type → Agent 的静态映射（route 节点消费）
    - 业务子图：管"具体干" —— 各 Agent 内部步骤（monitor / business_chat ...）

扩展点（二期）：
    1. 资金类写操作：aggregate 后加条件边 → approval 节点（对接广告审批闸门）
    2. 事件驱动：同一事件并行派发多个子图（并行分支，LangGraph 支持 fan-out/fan-in）
    3. 人工接管：子图内 interrupt() 后，由 runtime.resume_task() 恢复
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, START, StateGraph

from src.agents.registry import AgentRegistry
from src.agents.state import OrchestratorState
from src.constants import TaskStatus
from src.core.logger import logger

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


# ------------------------------------------------------------
# 节点实现
# ------------------------------------------------------------

def route_node(state: OrchestratorState, registry: AgentRegistry | None = None) -> dict[str, Any]:
    """路由节点：用注册表映射表把任务类型映射到目标 Agent。"""
    if registry is None:
        raise RuntimeError("route_node 缺少 registry（build 时未 partial 绑定）")
    task_type = state.get("task_type", "")
    spec = registry.route(task_type)
    logger.info(f"[Orchestrator] route: {task_type} → {spec.name}")
    return {"target_agent": str(spec.agent_type)}


def route_to_target(state: OrchestratorState) -> str:
    """条件边路由函数：返回目标子图节点名。"""
    target = state.get("target_agent")
    if not target:
        raise RuntimeError("未收到 target_agent（路由节点未执行？）")
    return target


def aggregate_node(state: OrchestratorState) -> dict[str, Any]:
    """聚合节点：归一化最终结果与状态，供 service 层落库/回写。

    子图节点输出（status/result/error/events/approval_no）已由 LangGraph
    自动合并进顶层状态，这里做最终归一化。
    """
    status = state.get("status", TaskStatus.SUCCESS)
    logger.info(f"[Orchestrator] aggregate: status={status}")
    return {
        "status": status,
        "result": state.get("result") or {},
    }


# ------------------------------------------------------------
# 编排图构建
# ------------------------------------------------------------

def build_orchestrator_graph(
    registry: AgentRegistry,
    checkpointer: Any | None = None,
) -> "CompiledStateGraph":
    """构建顶层调度中枢编排图。

    Args:
        registry: Agent 注册表（路由与子图查找）
        checkpointer: 检查点（memory/redis），子图 interrupt 依赖父图 checkpointer

    Returns:
        编译后的顶层编排图
    """
    graph = StateGraph(OrchestratorState)
    graph.add_node("route", partial(route_node, registry=registry))

    # 编译后的业务子图直接注册为顶层图节点（LangGraph 官方嵌套形态）
    route_map: dict[str, str] = {}
    for spec in registry.list_specs():
        key = str(spec.agent_type)
        graph.add_node(key, registry.get_graph(key))
        route_map[key] = key
        logger.info(f"[Orchestrator] 子图节点已挂载：{key}")

    # 增加聚合节点
    graph.add_node("aggregate", aggregate_node)

    # 增加路由边
    graph.add_edge(START, "route")
    # 增加条件路由边：route 之后按 target_agent 分发到对应子图节点
    graph.add_conditional_edges("route", route_to_target, route_map)
    # 每个子图节点结束后汇入聚合节点
    for key in route_map:
        graph.add_edge(key, "aggregate")
    graph.add_edge("aggregate", END)

    compiled = graph.compile(checkpointer=checkpointer)
    return compiled


__all__ = ["build_orchestrator_graph", "route_node", "route_to_target", "aggregate_node"]
