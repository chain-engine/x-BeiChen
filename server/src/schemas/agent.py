#!/usr/bin/env python3
"""Agent 编排域 Schema（任务提交 / 任务查询 / 事件查询 / 人工接管）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.constants import AgentType, TaskStatus


class AgentTaskCreate(BaseModel):
    """提交一个 Agent 任务。"""

    model_config = ConfigDict(use_enum_values=True)

    task_type: AgentType = Field(description="任务类型（路由到对应 Agent）")
    payload: dict[str, Any] = Field(default_factory=dict, description="任务入参（由各 Agent 自定义）")
    timeout_at: datetime | None = Field(default=None, description="超时时间，默认按配置")


class AgentTaskOut(BaseModel):
    """Agent 任务视图（响应）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: AgentType
    payload: dict[str, Any]
    status: TaskStatus
    assignee_agent: AgentType | None
    thread_id: str | None
    retry_count: int
    max_retries: int
    error_message: str | None
    result: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime | None


class AgentTaskResumeIn(BaseModel):
    """人工接管后恢复执行入参（interrupt/resume）。"""

    model_config = ConfigDict(use_enum_values=True)

    decision: str = Field(description="人工决策：approve / reject / adjust")
    remark: str | None = Field(default=None, description="人工备注")
    extra: dict[str, Any] = Field(default_factory=dict, description="附加数据（如调整后的预算数值）")


class AgentEventOut(BaseModel):
    """Agent 协作事件视图。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    source_agent: str | None
    target_agent: str | None
    payload: dict[str, Any] | None
    status: str | None
    created_at: datetime
