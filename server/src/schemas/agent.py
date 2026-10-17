#!/usr/bin/env python3
"""Agent 编排域 Schema（任务提交 / 人工接管入参）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.constants import AgentType


class AgentTaskCreate(BaseModel):
    """提交一个 Agent 任务。"""

    model_config = ConfigDict(use_enum_values=True)

    task_type: AgentType = Field(description="任务类型（路由到对应 Agent）")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "任务入参（按 task_type 选用对应字段）。"
            "monitor: {account_id?, campaign_id?}（account_id 默认 acc_default）；"
            "business_chat: {message!, customer_id?}（message 必填）；"
            "customer: {scope?（full/due_followup/by_ids/report，默认 due_followup）, "
            "customer_ids?（scope=by_ids 必填）, report_type?（daily/weekly）}"
        ),
    )
    timeout_at: datetime | None = Field(default=None, description="超时时间，默认按配置")


class AgentTaskResumeIn(BaseModel):
    """人工接管后恢复执行入参（interrupt/resume）。"""

    model_config = ConfigDict(use_enum_values=True)

    decision: str = Field(description="人工决策：approve / reject / adjust")
    remark: str | None = Field(default=None, description="人工备注")
    extra: dict[str, Any] = Field(default_factory=dict, description="附加数据（如调整后的预算数值）")
