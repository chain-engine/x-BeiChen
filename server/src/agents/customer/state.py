#!/usr/bin/env python3
"""客户管理 + 任务调度 Agent 子图状态（北辰 x-BeiChen）。

继承 AgentTaskState 获得顶层共享字段（status/result/error/events/approval_no），
扩展客户域私有字段（scope/customers/actions/tasks/report），仅存在于子图内部。
"""

from __future__ import annotations

from typing import Any

from src.agents.state import AgentTaskState


class CustomerState(AgentTaskState):
    """客户管理 + 任务调度子图状态。"""

    # ── 客户域私有字段 ──
    scope: str                     # 本轮巡检范围：full / due_followup / report
    customers: list[dict[str, Any]]  # 拉取到的客户状态快照列表
    actions: list[dict[str, Any]]    # 跟进判定出的动作清单（policy.build_followup_actions）
    tasks: list[dict[str, Any]]      # 编排出的任务清单（跟进任务 / 报表任务）
    report: dict[str, Any] | None    # 报表聚合结果（scope=report 时生成）
