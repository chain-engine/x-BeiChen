#!/usr/bin/env python3
"""Agent 编排层共享状态定义（北辰 x-BeiChen）。

状态即 LangGraph 图中流动的数据载体（TypedDict）：
    - OrchestratorState：顶层调度中枢状态（编排图专用字段）
    - AgentTaskState：任务通用状态（顶层与子图共享字段的"合并契约"）

字段约定：
    task_type / task_id —— 路由与审计
    payload —— 任务入参
    status / result / error —— 执行结果归一化
    events —— 协作事件累计（子图节点往这里追加，顶层聚合后落库）
    approval_no —— 资金类写操作的审批凭证（对齐广告审批留痕）
"""

from __future__ import annotations

from typing import Any, TypedDict


class OrchestratorState(TypedDict, total=False):
    """顶层编排图状态（调度中枢）。

    调度链路：route（映射表路由）→ subagent（调用子图）→ aggregate（聚合）。
    """

    task_id: int                    # 任务 ID（落库主键）
    task_type: str                  # 任务类型（路由键，AgentType.mark）
    payload: dict[str, Any]         # 任务入参
    target_agent: str | None        # route 节点写入：实际派发目标 Agent
    status: str                     # 执行状态（TaskStatus.mark）
    result: dict[str, Any] | None   # 最终结果（聚合节点写入）
    error: str | None               # 失败原因
    events: list[dict[str, Any]]    # 事件累计（子图节点追加）
    approval_no: str | None         # 资金类写操作的审批单号（广告审批凭证）


class AgentTaskState(TypedDict, total=False):
    """任务通用状态（子图状态建议以它为基底扩展业务字段）。

    子图内嵌顶层图时，LangGraph 会把子图输出的 dict 与顶层状态做同名键合并；
    因此子图状态必须声明 status / result / error / events / approval_no，
    才能将执行结果回传给顶层编排图。
    """

    task_id: int
    task_type: str
    payload: dict[str, Any]
    status: str
    result: dict[str, Any] | None
    error: str | None
    events: list[dict[str, Any]]
    approval_no: str | None
