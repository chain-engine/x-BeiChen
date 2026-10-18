#!/usr/bin/env python3
"""客户管理域 Schema（客户管理 Agent，演示）。

当前定位：演示 Agent（骨架期，业务需求未定稿）——Schema 承载 Agent 任务提交
（/customers/run）与报表触发 / 视图转换；客户数据管理（CRUD / 状态迁移）入参
属二期独立 CRM 模块，不在本文件。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReportTriggerIn(BaseModel):
    """报表触发入参（自动出报表，走 ReportService 确定性模板聚合，不经子图）。"""

    report_type: str = Field(default="daily", pattern="^(daily|weekly)$", description="日报/周报")
    customer_ids: list[str] | None = Field(default=None, description="指定客户（空=全量）")


class CustomerTaskIn(BaseModel):
    """提交客户管理 Agent 任务入参（POST /customers/run，走 customer 子图）。"""

    scope: str = Field(
        default="due_followup",
        pattern="^(due_followup|by_ids|full|report)$",
        description="巡检范围：due_followup 跟进到期（默认）/ by_ids 指定客户 / full 全量 / report 报表任务",
    )
    customer_ids: list[str] | None = Field(default=None, description="scope=by_ids 时必填")


def followup_to_dict(f: Any) -> dict:
    """跟进记录 ORM 实体 → 响应字典（Agent 产出的跟进任务视图）。"""
    return {
        "id": f.id,
        "customer_id": f.customer_id,
        "action": f.action,
        "content": f.content,
        "operator": f.operator,
        "next_followup_at": f.next_followup_at.isoformat() if f.next_followup_at else None,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


def report_to_dict(r: Any) -> dict:
    """报表 ORM 实体 → 响应字典。"""
    return {
        "id": r.id,
        "report_type": r.report_type,
        "customer_id": r.customer_id,
        "period_start": r.period_start.isoformat() if r.period_start else None,
        "period_end": r.period_end.isoformat() if r.period_end else None,
        "content": r.content,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def customer_view(task: Any) -> dict[str, Any]:
    """customer 子图任务实体 → 对话视图（跟进任务清单 / 报表产物）。"""
    result = task.result or {}
    return {
        "task_id": task.id,
        "status": task.status,
        "thread_id": task.thread_id,
        "followups": result.get("followups"),
        "report": result.get("report"),
        "db_persisted": result.get("db_persisted"),
    }
